import glob


def find(path):
	elems = path.split("/")

	parent = "/".join(elems[:-1])

	print(parent[-5:])

	if (parent[-5:] == "build") or (len(glob.glob(parent+"/*")) > 1):
		print("delete "+ path)

	else:
		print(path)
		find(parent)
		


path="build/stampede2/intel"

find(path)
