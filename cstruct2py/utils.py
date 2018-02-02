from .pycarray import BasePyArray

sizeof = len

def strcpy(src, limit=None):
	if isinstance(src, BasePyArray):
		src = src.packed

	if any(map(lambda x: isinstance(src, x), [str, bytearray])):
		indx = src.find("\x00")
		end = indx + 1 if indx != -1 else len(src)
		if limit != None:
			end = min(end, limit)

		return src[:end]

	raise TypeError("strcpy does not supprot %s type" % type(src).__name__)


