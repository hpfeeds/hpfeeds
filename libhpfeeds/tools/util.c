/*
  util.c
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

#include <ctype.h>
#include <stdio.h>
#include <sys/types.h>

// prints a hexdump
void hd(const u_char *data, size_t len) {
	register int i, j;

	if (!data || !len) return;

	for (i = 0; i < len; i += 0x10) {
		printf("0x%08x  ", i);

		for (j = 0; j < 0x10 && i+j<len; j++) {
			if (j == 0x8) putchar(' ');
			printf("%02x ", data[i+j]);
		}

		printf("%-*c|", (3 * (0x10 - j)) + (j > 0x8 ? 1 : 2), ' ');

		for (j = 0; j < 0x10 && i + j < len; j++)
			putchar(isprint(data[i+j]) ? data[i+j] : '.');

		puts("|");
	}
	putchar('\n');

	return;
}
