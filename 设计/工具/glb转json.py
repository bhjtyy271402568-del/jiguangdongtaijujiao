"""把 GLB 转成内嵌数据的 glTF JSON（网页发布只支持 .json，不支持 .glb）。用法：python glb转json.py 输入.glb 输出.json"""
import sys, json, struct, base64
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
magic, ver, length = struct.unpack_from("<4sII", b, 0); assert magic == b"glTF"
off = 12; js = None; binc = b""
while off < length:
    clen, ctype = struct.unpack_from("<II", b, off); data = b[off + 8: off + 8 + clen]
    if ctype == 0x4E4F534A: js = json.loads(data.decode("utf-8"))
    elif ctype == 0x004E4942: binc = data
    off += 8 + clen
js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binc).decode()
json.dump(js, open(dst, "w"), separators=(",", ":"))
print(f"{dst}: {len(open(dst,'rb').read())/1e6:.1f} MB")
