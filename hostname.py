
hostname = "c196-[041-047,051-052,061-062,071-072,082,091-092,101-102,111-112],c300-300, c197-[011-012,022,031-032,041-042,051-052,061,071-072,081-082,091-092,101-102,111-112],c198-[011-012,021-022,032,041-042,051-052,061-062,071-072,081-082,091-092,101,111-112],c199-[011-012,021-022,031-032,041-042,051-052,061-062,071-072,081-082,091-092,101-102,112,121], c200-420, c201-425"

prefix_len = 4

def get_suffixes(suf):
	answer = []
	suf_list = suf.split(',')
	for suf in suf_list:
		if '-' in suf:
			start, end = suf.split('-')
			tmp = range(int(start), int(end)+1)
			tmp = [str(t).zfill(3) for t in tmp]
			answer.extend(tmp)
		else:
			answer.append(suf)
	return answer

out_list = []
while hostname:
	if '[' in hostname:
		start = hostname.index('[')+1
		end = hostname.index(']')
		prefix = hostname[start-6:start-1]
		suffix = get_suffixes(hostname[start:end])
		out_list.extend([prefix + s for s in suffix])
		hostname = hostname[:start-6] + hostname[end+2:]
	else:
		additions = hostname.split(',')
		out_list.extend([s.strip() for s in additions])
		hostname = ''

out_list.sort()

print(', '.join(out_list))


