/*
  hpfeeds.h
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

#ifndef __hpfeeds_h
#define __hpfeeds_h

#include <sys/types.h>

#define	OP_ERROR 0
#define	OP_INFO	1
#define	OP_AUTH	2
#define	OP_PUBLISH 3
#define	OP_SUBSCRIBE 4

typedef struct {
	struct {
		u_int32_t msglen;
		u_int8_t opcode;
	}  __attribute__((__packed__)) hdr;
	u_char data[];
} hpf_msg_t;

typedef struct {
	u_char len;
	u_char data[];
} hpf_chunk_t;


void hpf_msg_delete(hpf_msg_t *m);

hpf_msg_t *hpf_msg_getmsg(u_char *data);
u_int32_t hpf_msg_getsize(hpf_msg_t *m);
u_int32_t hpf_msg_gettype(hpf_msg_t *m);

hpf_chunk_t *hpf_msg_get_chunk(u_char *data, size_t len);

hpf_msg_t *hpf_msg_error(u_char *err, size_t err_size);
hpf_msg_t *hpf_msg_info(u_int32_t nonce, u_char *fbname, size_t fbname_len);
hpf_msg_t *hpf_msg_auth(u_int32_t nonce, u_char *ident, size_t ident_len, u_char *secret, size_t secret_len);
hpf_msg_t *hpf_msg_publish(u_char *ident, size_t ident_len, u_char *channel, size_t channel_len, u_char *data, size_t data_len);
hpf_msg_t *hpf_msg_subscribe(u_char *ident, size_t ident_len, u_char *channel, size_t channel_len);

#endif
