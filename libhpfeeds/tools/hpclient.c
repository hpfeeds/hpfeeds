/*
  hpclient.h
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
#include <hpfeeds.h>
#include <stdio.h>
#include <stdlib.h>

#include "util.h"

char *msg_type2str(u_int32_t type) {
	switch (type) {
	case 0: return "OP_ERROR";
	case 1: return "OP_INFO";
	case 2: return "OP_AUTH";
	case 3: return "OP_PUBLISH";
	case 4: return "OP_SUBSCRIBE";
	}
	return "unknonwn";
}

int main(int argc, char *argv[]) {
	hpf_msg_t *msg;

	msg = hpf_msg_error((u_char *) "failure", 7);
	printf("message type %u (%s):\n", hpf_msg_gettype(msg), msg_type2str(hpf_msg_gettype(msg)));
	hd((u_char *) msg, ntohl(msg->hdr.msglen));
	if (msg) hpf_msg_delete(msg);
	
	msg = hpf_msg_info(123456789, (u_char *) "@hp1", 4);
	printf("message type %u (%s):\n", hpf_msg_gettype(msg), msg_type2str(hpf_msg_gettype(msg)));
	hd((u_char *) msg, ntohl(msg->hdr.msglen));
	if (msg) hpf_msg_delete(msg);

	msg = hpf_msg_auth(987654321, (u_char *) "test@hp1", 8, (u_char *) "secret", 6);
	printf("message type %u (%s):\n", hpf_msg_gettype(msg), msg_type2str(hpf_msg_gettype(msg)));
	hd((u_char *) msg, ntohl(msg->hdr.msglen));
	if (msg) hpf_msg_delete(msg);
	
	msg = hpf_msg_publish((u_char *) "test@hp1", 8, (u_char *) "testchannel", 11, (u_char *) "this is a test", 14);
	printf("message type %u (%s):\n", hpf_msg_gettype(msg), msg_type2str(hpf_msg_gettype(msg)));
	hd((u_char *) msg, ntohl(msg->hdr.msglen));
	if (msg) hpf_msg_delete(msg);

	msg = hpf_msg_subscribe((u_char *) "test@hp1", 8, (u_char *) "testchannel", 11);
	printf("message type %u (%s):\n", hpf_msg_gettype(msg), msg_type2str(hpf_msg_gettype(msg)));
	hd((u_char *) msg, ntohl(msg->hdr.msglen));
	if (msg) hpf_msg_delete(msg);
	
	return EXIT_SUCCESS;
}
