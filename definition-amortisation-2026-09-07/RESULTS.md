# Definition startup cost across authored conversations

No inference was run. Positive numbers mean MORE Ainglish text tokens. Replayed totals count every full request history plus its authored reply, not provider billing.

| Tokenizer | Guide policy | Turns | Transcript delta | Replayed-total delta | Largest Ainglish input |
|---|---|---:|---:|---:|---:|
| cl100k_base | once | 1 | 878.00 | 879.00 | 981 |
| cl100k_base | once | 2 | 869.00 | 1749.00 | 1056 |
| cl100k_base | once | 4 | 852.00 | 3463.00 | 1204 |
| cl100k_base | once | 8 | 812.00 | 6772.00 | 1503 |
| cl100k_base | once | 16 | 736.00 | 12936.00 | 2099 |
| cl100k_base | once | 32 | 584.00 | 23440.00 | 3291 |
| cl100k_base | once | 64 | 280.00 | 37152.00 | 5675 |
| cl100k_base | once | 128 | -328.00 | 35392.00 | 10443 |
| cl100k_base | each_turn | 1 | 878.00 | 879.00 | 981 |
| cl100k_base | each_turn | 2 | 1757.00 | 2637.00 | 1944 |
| cl100k_base | each_turn | 4 | 3516.00 | 8791.00 | 3868 |
| cl100k_base | each_turn | 8 | 7028.00 | 31636.00 | 7719 |
| cl100k_base | each_turn | 16 | 14056.00 | 119496.00 | 15419 |
| cl100k_base | each_turn | 32 | 28112.00 | 463888.00 | 30819 |
| cl100k_base | each_turn | 64 | 56224.00 | 1827360.00 | 61619 |
| cl100k_base | each_turn | 128 | 112448.00 | 7253056.00 | 123219 |
| o200k_base | once | 1 | 874.00 | 875.00 | 973 |
| o200k_base | once | 2 | 866.00 | 1742.00 | 1046 |
| o200k_base | once | 4 | 851.00 | 3453.00 | 1190 |
| o200k_base | once | 8 | 815.00 | 6768.00 | 1481 |
| o200k_base | once | 16 | 747.00 | 12992.00 | 2061 |
| o200k_base | once | 32 | 611.00 | 23808.00 | 3221 |
| o200k_base | once | 64 | 339.00 | 38912.00 | 5541 |
| o200k_base | once | 128 | -205.00 | 43008.00 | 10181 |
| o200k_base | each_turn | 1 | 874.00 | 875.00 | 973 |
| o200k_base | each_turn | 2 | 1749.00 | 2625.00 | 1929 |
| o200k_base | each_turn | 4 | 3500.00 | 8751.00 | 3839 |
| o200k_base | each_turn | 8 | 6996.00 | 31492.00 | 7662 |
| o200k_base | each_turn | 16 | 13992.00 | 118952.00 | 15306 |
| o200k_base | each_turn | 32 | 27984.00 | 461776.00 | 30594 |
| o200k_base | each_turn | 64 | 55968.00 | 1819040.00 | 61170 |
| o200k_base | each_turn | 128 | 111936.00 | 7220032.00 | 122322 |
| p50k_base | once | 1 | 953.00 | 953.00 | 1054 |
| p50k_base | once | 2 | 948.00 | 1901.00 | 1130 |
| p50k_base | once | 4 | 939.00 | 3783.00 | 1280 |
| p50k_base | once | 8 | 915.00 | 7476.00 | 1583 |
| p50k_base | once | 16 | 871.00 | 14600.00 | 2187 |
| p50k_base | once | 32 | 783.00 | 27792.00 | 3395 |
| p50k_base | once | 64 | 607.00 | 49952.00 | 5811 |
| p50k_base | once | 128 | 255.00 | 77376.00 | 10643 |
| p50k_base | each_turn | 1 | 953.00 | 953.00 | 1054 |
| p50k_base | each_turn | 2 | 1907.00 | 2860.00 | 2089 |
| p50k_base | each_turn | 4 | 3816.00 | 9537.00 | 4157 |
| p50k_base | each_turn | 8 | 7628.00 | 34328.00 | 8296 |
| p50k_base | each_turn | 16 | 15256.00 | 129680.00 | 16572 |
| p50k_base | each_turn | 32 | 30512.00 | 503456.00 | 33124 |
| p50k_base | each_turn | 64 | 61024.00 | 1983296.00 | 66228 |
| p50k_base | each_turn | 128 | 122048.00 | 7872128.00 | 132436 |

English is assumed known; Ainglish is taught with complete definitions. This is the current-incumbency scenario, not a causal training comparison. Cache discounts and actual model context limits are not simulated. No break-even proves comprehension or future efficiency.
