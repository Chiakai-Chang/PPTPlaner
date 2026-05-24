"""測試 agy -p 連續呼叫的行為"""
import time
from winpty import PtyProcess

def test_single_call(prompt):
    """測試單一呼叫"""
    cmd = f'agy -p "{prompt}" --dangerously-skip-permissions --print-timeout 60s'
    print(f"\n{'='*60}")
    print(f"執行: {cmd[:80]}...")
    
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
    import re
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', full_output)
    clean = re.sub(r'\x1b\?.*?[hH]', '', clean)
    
    print(f"時間: {elapsed:.1f}s")
    print(f"原始長度: {len(full_output)}")
    print(f"清理後長度: {len(clean)}")
    print(f"內容(前 200): {clean[:200]}")
    
    return clean.strip()

print("=" * 60)
print("測試 1: 第一次呼叫")
result1 = test_single_call('Respond with JSON: {"test": 1}')

print("\n" + "=" * 60)
print("測試 2: 第二次呼叫（同樣 prompt）")
time.sleep(2)  # 等待一下
result2 = test_single_call('Respond with JSON: {"test": 2}')

print("\n" + "=" * 60)
print("測試 3: 第三次呼叫（不同 prompt）")
time.sleep(2)
result3 = test_single_call("Say hello in 10 words")

print("\n" + "=" * 60)
print("結果摘要:")
print(f"測試 1: {len(result1)} chars")
print(f"測試 2: {len(result2)} chars")
print(f"測試 3: {len(result3)} chars")
