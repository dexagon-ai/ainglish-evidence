# Low-exposure tokenizer results

All 28 predeclared cells retained. These are small locally trained byte-level BPEs, not production tokenizers or model-weight training.

|Vocab|Presegmentation|Exposure|Nominal cap|A pair tokens|E pair tokens|Background English delta|Code delta|Unicode/punctuation delta|Lossless|
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
|8000|bytelevel-regex|baseline|0.000%|1692|1904|+0.000%|+0.000%|+0.000%|True|
|8000|bytelevel-regex|ainglish|0.100%|1666|1878|+0.011%|+0.000%|+0.000%|True|
|8000|bytelevel-regex|english|0.100%|1666|1878|+0.004%|+0.000%|+0.000%|True|
|8000|bytelevel-regex|ainglish|1.000%|1564|1800|+0.177%|+0.000%|+0.000%|True|
|8000|bytelevel-regex|english|1.000%|1602|1756|+0.176%|+0.000%|+0.000%|True|
|8000|bytelevel-regex|ainglish|5.000%|1490|1750|+0.168%|+2.105%|+1.445%|True|
|8000|bytelevel-regex|english|5.000%|1538|1678|+0.181%|+2.105%|+1.445%|True|
|8000|whitespace-preserving|baseline|0.000%|2392|2899|+0.000%|+0.000%|+0.000%|True|
|8000|whitespace-preserving|ainglish|0.100%|2348|2865|+0.007%|+0.000%|+0.000%|True|
|8000|whitespace-preserving|english|0.100%|2356|2857|+0.009%|+0.000%|+0.000%|True|
|8000|whitespace-preserving|ainglish|1.000%|2116|2738|+0.092%|-0.058%|-0.525%|True|
|8000|whitespace-preserving|english|1.000%|2228|2675|+0.076%|-0.058%|-0.525%|True|
|8000|whitespace-preserving|ainglish|5.000%|2028|2736|+0.112%|-1.110%|+0.525%|True|
|8000|whitespace-preserving|english|5.000%|2204|2621|+0.120%|-0.058%|+0.525%|True|
|16000|bytelevel-regex|baseline|0.000%|1512|1714|+0.000%|+0.000%|+0.000%|True|
|16000|bytelevel-regex|ainglish|0.100%|1504|1706|+0.004%|+0.000%|+0.000%|True|
|16000|bytelevel-regex|english|0.100%|1504|1706|+0.001%|+0.000%|+0.000%|True|
|16000|bytelevel-regex|ainglish|1.000%|1444|1660|+0.059%|+0.000%|+0.000%|True|
|16000|bytelevel-regex|english|1.000%|1464|1632|+0.054%|+0.000%|+0.000%|True|
|16000|bytelevel-regex|ainglish|5.000%|1420|1660|+0.099%|+2.326%|+0.000%|True|
|16000|bytelevel-regex|english|5.000%|1456|1608|+0.098%|+2.326%|-0.303%|True|
|16000|whitespace-preserving|baseline|0.000%|2292|2810|+0.000%|+0.000%|+0.000%|True|
|16000|whitespace-preserving|ainglish|0.100%|2266|2791|+0.002%|+0.000%|+0.000%|True|
|16000|whitespace-preserving|english|0.100%|2274|2787|+0.002%|+0.000%|+0.000%|True|
|16000|whitespace-preserving|ainglish|1.000%|2066|2699|+0.023%|-0.063%|+0.000%|True|
|16000|whitespace-preserving|english|1.000%|2178|2641|+0.013%|-0.063%|+0.000%|True|
|16000|whitespace-preserving|ainglish|5.000%|1974|2665|+0.091%|+1.752%|-0.279%|True|
|16000|whitespace-preserving|english|5.000%|2114|2567|+0.104%|+1.940%|+0.000%|True|

Positive collateral deltas mean more tokens, not improvement. Achieved A/English teaching byte shares differ: see PLAN.json. Paired evaluations share teaching frames but not lexical records. Full per-string counts and tokenizer hashes are retained. A failed lossless gate invalidates efficiency interpretation for that cell; it is not dropped.
