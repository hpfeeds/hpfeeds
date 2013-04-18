/*
  hpclient.c
  Copyright (C) 2011 The Honeynet Project
  Copyright (C) 2011 Tillmann Werner, tillmann.werner@gmx.de

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 2 as
  published by the Free Software Foundation.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <arpa/inet.h>
#include <getopt.h>
#include <hpfeeds.h>
#include <netdb.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAXLEN 1000000
#define READ_BLOCK_SIZE 32767

typedef enum {
S_INIT,
S_AUTH,
S_SUBSCRIBE,
S_PUBLISH,
S_RECVMSGS,
S_ERROR,
S_TERMINATE
} session_state_t;

session_state_t session_state;	// global session state

typedef enum {
C_SUBSCRIBE,
C_PUBLISH,
C_UNKNOWN } cmd_t;

u_char *read_msg(int s) {
	u_char *buffer;
	u_int32_t msglen;
	int len;
	int templen;
	char tempbuf[READ_BLOCK_SIZE];

	if (read(s, &msglen, 4) != 4) {
		perror("read()");
		exit(EXIT_FAILURE);
	}

	if ((buffer = malloc(ntohl(msglen))) == NULL) {
		perror("malloc()");
		exit(EXIT_FAILURE);
	}

	*(u_int32_t *) buffer = msglen;
	msglen = ntohl(msglen);

    len = 4;
    templen = len;
    while ((templen > 0) && (len < msglen)) {
        templen = read(s, tempbuf, READ_BLOCK_SIZE);
        memcpy(buffer + len, tempbuf, templen);
        len += templen;
    }

	if (len != msglen) {
		perror("read()");
		exit(EXIT_FAILURE);
	}

	return buffer;
}

void sigh(int sig) {
	switch (sig) {
	case SIGINT:
		if (session_state != S_TERMINATE) {
			if (write(STDOUT_FILENO, "\rSIGINT, signal again to terminate now.\n", 40) == -1) {
				perror("write()");
				exit(EXIT_FAILURE);
			}
			session_state = S_TERMINATE;
		} else {
			exit(EXIT_SUCCESS);
		}
		break;
	default:
		break;
	}
	return;
}

void usage(char *argv0) {
        fprintf(stderr, "Usage: %s -h host -p port [ -S | -P ] -c channel -i ident -s secret\n", argv0);
        fprintf(stderr, "       -S subscribe to channel, print msg to stdout\n");
        fprintf(stderr, "       -P publish   to channel, read msg from stdin\n");
}

int main(int argc, char *argv[]) {
	cmd_t hpfdcmd;
	hpf_msg_t *msg;
	hpf_chunk_t *chunk;
	u_char *data;
	char *errmsg, *channel, *ident, *secret;
	int s, opt;
	struct hostent *he;
	struct sockaddr_in host;
	u_int32_t nonce = 0;
	u_int32_t payload_len;
	u_char* buf;
	int len;
	int templen;
	char tempbuf[READ_BLOCK_SIZE];

	buf = (u_char*)malloc(sizeof(u_char) * MAXLEN);

	hpfdcmd = C_UNKNOWN;
	channel = NULL;
	ident = NULL;
	secret = NULL;
	msg = NULL;

	memset(&host, 0, sizeof(struct sockaddr_in));
	host.sin_family = AF_INET;

	while ((opt = getopt(argc, argv, "SPc:h:i:p:s:")) != -1) {
		switch (opt) {
		case 'S':
			hpfdcmd = C_SUBSCRIBE;
			break;
		case 'P':
			hpfdcmd = C_PUBLISH;
			break;
		case 'c':
			channel = optarg;
			break;
		case 'h':
			if ((he = gethostbyname(optarg)) == NULL) {
				perror("gethostbyname()");
				exit(EXIT_FAILURE);
			}

			if (he->h_addrtype != AF_INET) {
				fprintf(stderr, "Unsupported address type\n");
				exit(EXIT_FAILURE);
			}

			host.sin_addr = *(struct in_addr *) he->h_addr;

			break;
		case 'i':
			ident = optarg;
			break;
		case 'p':
			host.sin_port = htons(strtoul(optarg, 0, 0));

			break;
		case 's':
			secret = optarg;
			break;
		default:
			usage(argv[0]);
			exit(EXIT_FAILURE);
		}
	}

	if (hpfdcmd == C_UNKNOWN || !channel || !ident || !secret || host.sin_addr.s_addr == INADDR_ANY || host.sin_port == 0) {
		usage(argv[0]);
		exit(EXIT_FAILURE);
	}

	// install sigint handler
	if (signal(SIGINT, sigh) == SIG_ERR) {
		perror("signal()");
		exit(EXIT_FAILURE);
	}

	// connect to broker
	if ((s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1) {
		perror("socket()");
		exit(EXIT_FAILURE);
	}
	fprintf(stderr, "connecting to %s:%u\n", inet_ntoa(host.sin_addr), ntohs(host.sin_port));
	if (connect(s, (struct sockaddr *) &host, sizeof(host)) == -1) {
		perror("connect()");
		exit(EXIT_FAILURE);
	}

	session_state = S_INIT; // initial session state

	// this is our little session state machine
	for (;;) switch (session_state) {
	case S_INIT:
		// read info message
		if ((data = read_msg(s)) == NULL) break;
		msg = (hpf_msg_t *) data;

		switch (msg->hdr.opcode) {
		case OP_INFO:

			chunk = hpf_msg_get_chunk(data + sizeof(msg->hdr), ntohl(msg->hdr.msglen) - sizeof(msg->hdr));
			if (chunk == NULL) {
				fprintf(stderr, "invalid message format\n");
				exit(EXIT_FAILURE);
			}

			nonce = *(u_int32_t *) (data + sizeof(msg->hdr) + chunk->len + 1);

			session_state = S_AUTH;

			free(data);

			break;
		case OP_ERROR:
			session_state = S_ERROR;
			break;
		default:
			fprintf(stderr, "unknown server message (type %u)\n", msg->hdr.opcode);
			exit(EXIT_FAILURE);
		}

		break;
	case S_AUTH:
		// send auth message
		fprintf(stderr, "sending authentication...\n");
		msg = hpf_msg_auth(nonce, (u_char *) ident, strlen(ident), (u_char *) secret, strlen(secret));

		if (write(s, (u_char *) msg, ntohl(msg->hdr.msglen)) == -1) {
			perror("write()");
			exit(EXIT_FAILURE);
		}
		hpf_msg_delete(msg);

		if (hpfdcmd == C_SUBSCRIBE)
			session_state = S_SUBSCRIBE;
		else
			session_state = S_PUBLISH;
		break;
	case S_SUBSCRIBE:
		// send subscribe message
		fprintf(stderr, "subscribing to channel...\n");
		msg = hpf_msg_subscribe((u_char *) ident, strlen(ident), (u_char *) channel, strlen(channel));

		if (write(s, (u_char *) msg, ntohl(msg->hdr.msglen)) == -1) {
			perror("write()");
			exit(EXIT_FAILURE);
		}
		hpf_msg_delete(msg);

		session_state = S_RECVMSGS;
		break;
	case S_RECVMSGS:
		// read server message
		if ((data = read_msg(s)) == NULL) break;
		msg = (hpf_msg_t *) data;

		switch (msg->hdr.opcode) {
		case OP_PUBLISH:
			// skip chunks
			payload_len = hpf_msg_getsize(msg) - sizeof(msg->hdr);

			chunk = hpf_msg_get_chunk(data + sizeof(msg->hdr), ntohl(msg->hdr.msglen) - sizeof(msg->hdr));
			if (chunk == NULL) {
				fprintf(stderr, "invalid message format\n");
				exit(EXIT_FAILURE);
			}
			payload_len -= chunk->len + 1;

			chunk = hpf_msg_get_chunk(data + sizeof(msg->hdr) + chunk->len + 1, ntohl(msg->hdr.msglen) - sizeof(msg->hdr) - chunk->len - 1);
			if (chunk == NULL) {
				fprintf(stderr, "invalid message format\n");
				exit(EXIT_FAILURE);
			}
			payload_len -= chunk->len + 1;

			if (write(STDOUT_FILENO, data + hpf_msg_getsize(msg) - payload_len, payload_len) == -1) {
				perror("write()");
				exit(EXIT_FAILURE);
			}
			putchar('\n');

			free(data);

			// we just remain in S_SUBSCRIBED
			break;
		case OP_ERROR:
			session_state = S_ERROR;
			break;
		default:
			fprintf(stderr, "unknown server message (type %u)\n", msg->hdr.opcode);
			exit(EXIT_FAILURE);
		}

		break;
	case S_PUBLISH:
		// send publish message
		len = 0;
		templen = 0;
		memset(tempbuf, 0x0, READ_BLOCK_SIZE);
		while ((templen = read(STDIN_FILENO, tempbuf, READ_BLOCK_SIZE)) > 0 && len < MAXLEN) {
		    memcpy(buf + len, tempbuf, templen);
		    len += templen;
			if(buf[len - 1] == '\n') {
				buf[len - 1] = 0;
				len --;
			}
		}
		fprintf(stderr, "publish %d bytes to channel...\n", len);
		msg = hpf_msg_publish((u_char *) ident, strlen(ident), (u_char *) channel, strlen(channel),buf,len);
		if (write(s, (u_char *) msg, ntohl(msg->hdr.msglen)) == -1) {
			perror("write()");
			exit(EXIT_FAILURE);
		}
		close(s);
		hpf_msg_delete(msg);
		exit(EXIT_SUCCESS);
		break;
		break;
	case S_ERROR:
		if (msg) {
			// msg is still valid
			if ((errmsg = calloc(1, msg->hdr.msglen - sizeof(msg->hdr))) == NULL) {
				perror("calloc()");
				exit(EXIT_FAILURE);
			}
            memcpy(errmsg, msg->data, ntohl(msg->hdr.msglen) - sizeof(msg->hdr));

			fprintf(stderr, "server error: '%s'\n", errmsg);
			free(errmsg);

			free(msg);
		}

		session_state = S_TERMINATE;
		break;
	case S_TERMINATE:
		fprintf(stderr, "terminated.\n");
		close(s);
		return EXIT_SUCCESS;
	default:
		fprintf(stderr, "unknown session state\n");
		close(s);
		exit(EXIT_FAILURE);
	}

	close(s);

	return EXIT_SUCCESS;
}
