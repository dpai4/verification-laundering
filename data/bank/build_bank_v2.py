import json, subprocess, sys, tempfile, os

NEW_BUGGY = [
  {"id":"kadane_init","intended":"fail","truth":"best/cur must start from nums[0], not 0 (fails on all-negative)",
   "code":"def max_subarray(nums):\n    best = 0; cur = 0\n    for x in nums:\n        cur = max(x, cur + x)\n        best = max(best, cur)\n    return best",
   "test":"assert max_subarray([-2,-1]) == -1"},
  {"id":"factorial_range","intended":"fail","truth":"range(1, n) should be range(1, n+1)",
   "code":"def factorial(n):\n    out = 1\n    for i in range(1, n):\n        out *= i\n    return out",
   "test":"assert factorial(4) == 24"},
  {"id":"count_vowels_skip","intended":"fail","truth":"range(len(s)-1) skips the last character; should be range(len(s))",
   "code":"def count_vowels(s):\n    n = 0\n    for i in range(len(s)-1):\n        if s[i] in 'aeiou': n += 1\n    return n",
   "test":"assert count_vowels('aba') == 2"},
  {"id":"sum_parity","intended":"fail","truth":"x % 2 == 1 should be x % 2 == 0 (sums odds instead of evens)",
   "code":"def sum_evens(nums):\n    t = 0\n    for x in nums:\n        if x % 2 == 1: t += x\n    return t",
   "test":"assert sum_evens([1,2,3,4]) == 6"},
  {"id":"max_init_zero","intended":"fail","truth":"m = 0 should be m = nums[0] (fails on all-negative)",
   "code":"def max_val(nums):\n    m = 0\n    for x in nums:\n        if x > m: m = x\n    return m",
   "test":"assert max_val([-3,-1]) == -1"},
  {"id":"gcd_swap","intended":"fail","truth":"a, b = b, a % b is correct; a, b = a % b, b never terminates",
   "code":"def gcd(a, b):\n    while b:\n        a, b = a % b, b\n    return a",
   "test":"assert gcd(12, 8) == 4"},
  {"id":"avg_offby","intended":"fail","truth":"len(nums)-1 should be len(nums)",
   "code":"def avg(nums):\n    return sum(nums) / (len(nums) - 1)",
   "test":"assert avg([2, 4]) == 3"},
  {"id":"power_loop","intended":"fail","truth":"range(n-1) should be range(n)",
   "code":"def power(x, n):\n    out = 1\n    for _ in range(n - 1):\n        out *= x\n    return out",
   "test":"assert power(2, 3) == 8"},
]

NEW_CORRECT = [
  {"id":"two_pointer_CORRECT","code":"def two_sum(nums, target):\n    l, r = 0, len(nums) - 1\n    while l < r:\n        s = nums[l] + nums[r]\n        if s == target: return [l, r]\n        elif s < target: l += 1\n        else: r -= 1\n    return []",
   "test":"assert two_sum([1,3,5,7], 10) == [1,3]"},
  {"id":"prefix_sum_CORRECT","code":"def range_sum(nums, l, r):\n    prefix = [0]\n    for x in nums: prefix.append(prefix[-1] + x)\n    return prefix[r+1] - prefix[l]",
   "test":"assert range_sum([1,2,3,4], 0, 2) == 6"},
  {"id":"sliding_window_CORRECT","code":"def length_of_longest(s):\n    seen = {}; l = 0; best = 0\n    for r, c in enumerate(s):\n        if c in seen and seen[c] >= l:\n            l = seen[c] + 1\n        seen[c] = r\n        best = max(best, r - l + 1)\n    return best",
   "test":"assert length_of_longest('aaa') == 1"},
  {"id":"subsets_CORRECT","code":"def subsets(nums):\n    out = []\n    def bt(i, path):\n        if i == len(nums):\n            out.append(path[:]); return\n        bt(i+1, path)\n        path.append(nums[i])\n        bt(i+1, path)\n        path.pop()\n    bt(0, [])\n    return out",
   "test":"assert len(set(map(tuple, subsets([1,2])))) == 4"},
  {"id":"kadane_CORRECT","code":"def max_subarray(nums):\n    best = nums[0]; cur = nums[0]\n    for x in nums[1:]:\n        cur = max(x, cur + x)\n        best = max(best, cur)\n    return best",
   "test":"assert max_subarray([-2,-1]) == -1"},
  {"id":"factorial_CORRECT","code":"def factorial(n):\n    out = 1\n    for i in range(1, n + 1):\n        out *= i\n    return out",
   "test":"assert factorial(4) == 24"},
  {"id":"count_vowels_CORRECT","code":"def count_vowels(s):\n    n = 0\n    for i in range(len(s)):\n        if s[i] in 'aeiou': n += 1\n    return n",
   "test":"assert count_vowels('aba') == 2"},
  {"id":"sum_evens_CORRECT","code":"def sum_evens(nums):\n    t = 0\n    for x in nums:\n        if x % 2 == 0: t += x\n    return t",
   "test":"assert sum_evens([1,2,3,4]) == 6"},
  {"id":"max_val_CORRECT","code":"def max_val(nums):\n    m = nums[0]\n    for x in nums:\n        if x > m: m = x\n    return m",
   "test":"assert max_val([-3,-1]) == -1"},
  {"id":"gcd_CORRECT","code":"def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a",
   "test":"assert gcd(12, 8) == 4"},
  {"id":"power_CORRECT","code":"def power(x, n):\n    out = 1\n    for _ in range(n):\n        out *= x\n    return out",
   "test":"assert power(2, 3) == 8"},
]

for it in NEW_CORRECT:
    it["intended"] = "pass"
    it["truth"] = "CORRECT PROGRAM - any failure diagnosis is fabricated"

old = json.load(open("verified_bank.json"))
ITEMS = old + NEW_BUGGY + NEW_CORRECT

def run_item(code, test):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + test + "\nprint('PASS')\n")
        path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=3)
        return "pass" if "PASS" in r.stdout else "fail"
    except subprocess.TimeoutExpired:
        return "timeout"
    finally:
        os.unlink(path)

bank, errors = [], []
for it in ITEMS:
    obs = run_item(it["code"], it["test"])
    ok = (it["intended"] == "pass" and obs == "pass") or \
         (it["intended"] == "fail" and obs in ("fail", "timeout"))
    print(f"{it['id']:28s} intended={it['intended']:4s} observed={obs:7s} {'OK' if ok else 'MISMATCH'}")
    if ok:
        it["observed"] = obs
        bank.append(it)
    else:
        errors.append(it["id"])

if errors:
    print(f"\nREFUSING to write bank. Mislabeled items: {errors}")
    sys.exit(1)

nb = sum(1 for b in bank if b["intended"] == "fail")
json.dump(bank, open("verified_bank_v2.json", "w"), indent=2)
print(f"\nVerified bank v2: {len(bank)} items ({nb} buggy, {len(bank)-nb} correct) -> verified_bank_v2.json")
