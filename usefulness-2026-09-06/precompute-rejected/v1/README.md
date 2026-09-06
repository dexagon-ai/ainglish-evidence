# Pre-compute draft refused; zero training or target calls

The first preparation audit found that balancing each family separately still
left aggregate training labels at A58/B58/C52. Six families had their remainder
rows assigned to the same positions. The source generator was changed to continue
the global rotation between families. The corrected prospective corpus is
A56/B56/C56; evaluation is A84/B84/C84. No outcome was observed when this change
was made. These superseded unspent draft files are retained for transparency and
are not additional training or evaluation samples.
