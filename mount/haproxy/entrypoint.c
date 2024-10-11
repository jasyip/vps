#include <stdbool.h>  // for bool, false, true
#include <stdio.h>    // for fputs, stderr, perror, fclose, fflush, fopen
#include <stdlib.h>   // for getenv, malloc
#include <string.h>   // for memcpy, memmove, strcmp
#include <unistd.h>   // for execvp

#define DEFAULT_CMD "haproxy"

int main(int const argc, char const * const argv[]) {
	bool successful_mta = false;
	if (argc < 3) {
		fputs("Must provide MTA file path and command\n", stderr);
		goto exit;
	}
	FILE * const f = fopen(argv[1], "a");
	if (!f) {
		perror("Error reading config file");
		goto exit;
	}
	char const * const subdomain = getenv("MX_SUBDOMAIN");
	if (!subdomain || !subdomain[0]) {
		fputs("ERROR: $MX_SUBDOMAIN is missing or empty\n", stderr);
		goto close_f;
	}
	char const * const domain = getenv("DOMAIN");
	if (!domain || !domain[0]) {
		fputs("ERROR: $DOMAIN is missing or empty\n", stderr);
		goto close_f;
	}

	if (fprintf(f, "mx: %s.%s\n", subdomain, domain) == -1) {
		fputs("Error appending to file\n", stderr);
		goto close_f;
	}
	successful_mta = true;

close_f:
	if (fclose(f) == -1) {
		fputs("Error closing file\n", stderr);
		goto exit;
	}

	if (!successful_mta) {
		goto exit;
	}

	char ** const new_argv = malloc(sizeof(char *) * (argc + 2));
	if (!new_argv) {
		fputs("Couldn't allocate memory for new argument array\n", stderr);
		goto exit;
	}
	new_argv[0]             = DEFAULT_CMD;
	bool const provided_cmd = argv[2][0] != '-';
	memcpy(new_argv + !provided_cmd, argv + 2, sizeof(char *) * (argc - 1));
	if (!strcmp(new_argv[0], DEFAULT_CMD)) {
		memmove(new_argv + 3,
		        new_argv + 1,
		        sizeof(char *) * (argc - provided_cmd));
		new_argv[1] = "-W";
		new_argv[2] = "-db";
	}
	fflush(stderr);
	execvp(new_argv[0], new_argv);
	perror("Error executing " DEFAULT_CMD);
exit:
	return 1;
}
