#!/usr/bin/env python3
"""Live end-to-end test of lumix-mcp through a real MCP client (stdio). Needs a camera on USB.

  python tests/live_mcp_test.py [--write]   (--write also tests settings, upload/delete of a test LUT, capture)

Everything it changes is put back: settings via restore_settings, the test LUT is deleted.
"""
import asyncio, json, os, sys, tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))
WRITE = '--write' in sys.argv


def text(res):
    if res.is_error:
        return 'ERROR: ' + ' '.join(getattr(c, 'text', '') for c in res.content)
    sc = getattr(res, 'structured_content', None)
    return sc if sc is not None else ' '.join(getattr(c, 'text', '') for c in res.content)


async def main():
    params = StdioServerParameters(command=os.path.join(os.path.dirname(sys.executable), 'lumix-mcp'), args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print('tools:', len(tools.tools))
            st = text(await s.call_tool('selftest', {}))
            print('selftest:', json.dumps(st, default=str)[:400])
            lib = text(await s.call_tool('list_luts', {}))
            print('list_luts:', len(lib.get('result', lib)) if isinstance(lib, dict) else lib)
            if not WRITE:
                return
            print('set_white_balance kelvin 5600:', text(await s.call_tool('set_white_balance', {'mode': 'kelvin', 'kelvin': 5600})))
            print('restore_settings:', text(await s.call_tool('restore_settings', {})))
            tmp = os.path.join(tempfile.mkdtemp(), 'mcp_test.cube')
            print('write_lut_file:', text(await s.call_tool('write_lut_file', {
                'source': os.path.join(HERE, '..', 'examples', 'luts', 'identity_std.cube'), 'destination': tmp,
                'grain': 50, 'color_noise': 0, 'title': 'MCP test'})))
            print('upload_lut:', text(await s.call_tool('upload_lut', {'path': tmp, 'name': 'MCP test', 'grain': 50, 'color_noise': 0})))
            print('delete without confirm:', text(await s.call_tool('delete_lut', {'name': 'MCP test'})))
            res = text(await s.call_tool('delete_lut', {'name': 'MCP test', 'confirm': True}))
            print('delete with confirm, last entries:', (res.get('result', res) if isinstance(res, dict) else res)[-2:])
            print('capture:', json.dumps(text(await s.call_tool('capture', {'output_dir': tempfile.mkdtemp(), 'basename': 'mcp_capture'})), default=str)[:500])


asyncio.run(main())
