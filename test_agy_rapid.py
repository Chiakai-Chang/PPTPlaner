"""測試 agy -p 快速連續呼叫（模擬 orchestrate 行為）"""
import time
from winpty import PtyProcess
import re

def agy_call(prompt, call_num):
    """模擬 adapter 呼叫"""
    cmd = f'agy -p "{prompt}" --dangerously-skip-permissions --print-timeout 60s'
    
    print(f"\n--- 呼叫 #{call_num} ---")
    print(f"Command: {cmd[:100]}...")
    
    proc = PtyProcess.spawn(cmd)
    full_output = ""
    
    start = time.time()
    while proc.isalive():
        try:
            chunk = proc.read(4096)
            if chunk:
                full_output += chunk
        except EOFError:
            break
        time.sleep(0.1)
    
    elapsed = time.time() - start
    
    # 清理 ANSI codes
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', full_output)
    clean = re.sub(r'\x1b\?.*?[hH]', '', clean)
    
    print(f"時間: {elapsed:.1f}s")
    print(f"清理後長度: {len(clean)}")
    print(f"內容(前 300): {repr(clean[:300])}")
    
    return clean.strip(), len(clean)

# 模擬 orchestrate 的行為：多次呼叫同樣的 prompt
print("=" * 70)
print("模擬 orchestrate: 快速連續呼叫")
print("=" * 70)

prompt = 'Respond with JSON containing a detailed analysis with at least 200 characters'

for i in range(6):
    result, length = agy_call(prompt, i + 1)
    time.sleep(1)  # 模擬實際間隔

print("\n" + "=" * 70)
print("結果摘要:")
print(f"所有呼叫都完成，沒有崩潰")
