def normalize_candidate(nums, ests, rng):
    nums = list(dict.fromkeys(n for n in nums if 1 <= n <= 50))
    ests = list(dict.fromkeys(e for e in ests if 1 <= e <= 12))
    while len(nums) < 5:
        n = rng.randint(1, 50)
        if n not in nums:
            nums.append(n)
    while len(ests) < 2:
        e = rng.randint(1, 12)
        if e not in ests:
            ests.append(e)
    return sorted(nums[:5]), sorted(ests[:2])


def gaps(nums):
    s = sorted(nums)
    return [s[i + 1] - s[i] for i in range(4)]
