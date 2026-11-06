"""Run a local optical-analysis job through the verified Zemax stdio MCP server."""
import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).parent
REPO = ROOT.parent / 'Zemax_MCP_适配检查_2026-11-05' / 'zemax-mcp-server-main'
JOB = Path(sys.argv[1]).resolve()
LOG = ROOT / (JOB.stem + '_MCP记录.json')
records = []


async def main():
    env = {**os.environ, 'PYTHONPATH': str(REPO), 'PYTHONNET_RUNTIME': 'netfx',
           'PYTHONIOENCODING': 'utf-8', 'ZEMAX_MCP_ALLOW_EVAL': '1'}
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / 'mcp_bootstrap.py')],
                                  cwd=str(REPO), env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(minutes=30)) as client:
            await client.initialize()

            async def call(name, args):
                response = await client.call_tool(name, args)
                payload = response.structuredContent
                if payload is None:
                    text = next(c.text for c in response.content if c.type == 'text')
                    try:
                        payload = json.loads(text)
                    except ValueError:
                        payload = {'text': text}
                payload.pop('serial', None)
                records.append({'tool': name, 'error': bool(response.isError), 'result': payload})
                LOG.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
                rendered = json.dumps(payload, ensure_ascii=False)
                print(name, rendered if len(rendered) < 1200 else rendered[:1200] + ' ... [full result in log]', flush=True)
                assert not response.isError and payload.get('ok'), payload
                return payload

            await call('zemax_connect', {'mode': 'standalone'})
            try:
                source = JOB.read_text(encoding='utf-8')
                code = ('import traceback\ntry:\n    exec(compile(' + repr(source) + ', ' + repr(str(JOB)) + ", 'exec'), globals())\n"
                        'except Exception:\n    raise RuntimeError(traceback.format_exc())')
                await call('zemax_eval', {'code': code})
            finally:
                await call('zemax_disconnect', {})


asyncio.run(main())
