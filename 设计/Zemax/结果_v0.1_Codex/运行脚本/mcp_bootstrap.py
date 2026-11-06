"""Keep native OpticStudio diagnostic output out of the MCP JSON stream."""
import ctypes
import io
import os
import sys

protocol_fd = os.dup(sys.stdout.fileno())
os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetStdHandle.argtypes = [ctypes.c_ulong]
kernel.GetStdHandle.restype = ctypes.c_void_p
kernel.SetStdHandle.argtypes = [ctypes.c_ulong, ctypes.c_void_p]
kernel.SetStdHandle.restype = ctypes.c_int
kernel.SetStdHandle(0xFFFFFFF5, kernel.GetStdHandle(0xFFFFFFF4))
sys.stdout = io.TextIOWrapper(os.fdopen(protocol_fd, 'wb', buffering=0), encoding='utf-8', write_through=True)

from zemax_mcp.server import main
main()
