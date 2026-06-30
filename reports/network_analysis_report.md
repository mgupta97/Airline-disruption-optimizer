# Airline Network Analysis Report

This report converts flight-level data into an airport-route network. Nodes represent airports, directed edges represent origin-destination routes, and risk scores combine delay performance with network importance.

## Network Summary

| metric                            |     value |
|:----------------------------------|----------:|
| flights                           | 539747    |
| airports                          |    269    |
| routes_used_for_network           |   3171    |
| average_arrival_delay_15_rate_pct |     18.18 |
| average_cancellation_rate_pct     |      3.02 |

## Top Airports by Disruption Risk

| airport   |   departing_flights |   arrival_delay_15_rate |   cancellation_rate |   network_criticality_score |   airport_disruption_risk_score |
|:----------|--------------------:|------------------------:|--------------------:|----------------------------:|--------------------------------:|
| DCA       |               11734 |                   21.12 |                9.35 |                      0.9633 |                          0.8223 |
| ASE       |                1025 |                   31.71 |                5.27 |                      0.6163 |                          0.8205 |
| HSV       |                 663 |                   30.47 |                6.18 |                      0.5675 |                          0.809  |
| ATL       |               23881 |                   21.97 |                5.23 |                      0.9909 |                          0.8062 |
| CRW       |                 231 |                   30.3  |               11.69 |                      0.4198 |                          0.7997 |
| DFW       |               25124 |                   20.25 |                6.34 |                      1      |                          0.7828 |
| MGM       |                 192 |                   27.6  |               10.42 |                      0.3964 |                          0.7739 |
| COU       |                 148 |                   27.7  |                9.46 |                      0.3833 |                          0.7625 |
| PHL       |                6688 |                   23.83 |                2.77 |                      0.9072 |                          0.7592 |
| SYR       |                 912 |                   26.43 |                3.07 |                      0.6886 |                          0.7508 |
| SDF       |                1701 |                   21.34 |                6.29 |                      0.7772 |                          0.7488 |
| CHA       |                 478 |                   24.9  |                5.86 |                      0.5314 |                          0.7438 |
| GCC       |                  62 |                   30.65 |                9.68 |                      0.2639 |                          0.73   |
| LEX       |                 626 |                   21.88 |                7.03 |                      0.55   |                          0.7286 |
| ALB       |                 882 |                   24.94 |                3.06 |                      0.6721 |                          0.7283 |
| BUF       |                1396 |                   24.43 |                2.79 |                      0.7444 |                          0.7277 |
| DEN       |               24732 |                   24.56 |                1.27 |                      0.9966 |                          0.725  |
| IAD       |                4008 |                   21.46 |                3.14 |                      0.8714 |                          0.7233 |
| HDN       |                 346 |                   31.5  |                4.34 |                      0.3717 |                          0.7229 |
| DAY       |                 581 |                   25.13 |                3.79 |                      0.5465 |                          0.721  |

## Top Airports by Network Criticality

| airport   |   departing_flights |   total_weighted_degree |   total_route_degree |   pagerank |   betweenness_centrality |   network_criticality_score |
|:----------|--------------------:|------------------------:|---------------------:|-----------:|-------------------------:|----------------------------:|
| DFW       |               25124 |                   48901 |                  296 |  0.0583192 |               0.295897   |                      1      |
| DEN       |               24732 |                   47477 |                  260 |  0.0523319 |               0.224363   |                      0.9966 |
| ATL       |               23881 |                   46341 |                  218 |  0.0415333 |               0.0873815  |                      0.9909 |
| ORD       |               21643 |                   41616 |                  224 |  0.0410122 |               0.128552   |                      0.9908 |
| CLT       |               16877 |                   32714 |                  200 |  0.0317501 |               0.0876668  |                      0.9873 |
| PHX       |               15956 |                   30397 |                  158 |  0.0271739 |               0.048586   |                      0.9783 |
| SEA       |               11882 |                   22404 |                  110 |  0.0216041 |               0.0722327  |                      0.9746 |
| LAX       |               15157 |                   29043 |                  120 |  0.0236556 |               0.0197564  |                      0.9704 |
| MCO       |               13058 |                   25229 |                  118 |  0.0209824 |               0.0255028  |                      0.9657 |
| LAS       |               15007 |                   27808 |                  126 |  0.0224008 |               0.0103014  |                      0.9647 |
| DCA       |               11734 |                   21989 |                  134 |  0.018988  |               0.0261104  |                      0.9633 |
| SLC       |                9350 |                   17596 |                  136 |  0.0182323 |               0.053136   |                      0.9605 |
| SFO       |               10839 |                   20522 |                  106 |  0.0179572 |               0.0272056  |                      0.9598 |
| DTW       |                9253 |                   17189 |                  124 |  0.017015  |               0.0531115  |                      0.9548 |
| MSP       |                8483 |                   14846 |                  118 |  0.0165369 |               0.0609172  |                      0.9523 |
| IAH       |                9250 |                   16763 |                   98 |  0.0151294 |               0.0272089  |                      0.9458 |
| LGA       |               10905 |                   20950 |                   94 |  0.0172434 |               0.00644275 |                      0.9454 |
| EWR       |               10144 |                   19169 |                   95 |  0.0154521 |               0.00755175 |                      0.9417 |
| MIA       |               10182 |                   19055 |                   98 |  0.015391  |               0.00620231 |                      0.9338 |
| JFK       |                8327 |                   15948 |                   82 |  0.012681  |               0.00782406 |                      0.9334 |

## Top Routes by Delay Risk

| route      |   flights |   arrival_delay_15_rate |   arrival_delay_60_rate |   cancellation_rate |   avg_arrival_delay |   route_delay_risk_score |
|:-----------|----------:|------------------------:|------------------------:|--------------------:|--------------------:|-------------------------:|
| BOS -> PBI |       238 |                   41.6  |                   13.45 |                0.84 |               20.82 |                   227.82 |
| GRR -> DFW |        75 |                   50.67 |                   16    |                6.67 |               29.76 |                   219.44 |
| ORD -> ASE |       143 |                   44.06 |                   18.18 |                0.7  |               21.91 |                   218.97 |
| SFB -> USA |        12 |                   83.33 |                   33.33 |                0    |               56.83 |                   213.74 |
| HSV -> DFW |       176 |                   40.91 |                   14.2  |                8.52 |               33.53 |                   211.76 |
| BDL -> SJU |        96 |                   45.83 |                   12.5  |                1.04 |               29.35 |                   209.66 |
| IAH -> EGE |        37 |                   56.76 |                    8.11 |                2.7  |               17.03 |                   206.47 |
| DEN -> COS |       436 |                   33.94 |                   11.47 |                0.46 |               16.01 |                   206.35 |
| HSV -> DCA |       104 |                   44.23 |                   24.04 |               11.54 |               51.87 |                   205.84 |
| DEN -> LBB |        71 |                   47.89 |                   23.94 |                0    |               26.07 |                   204.81 |
| MDW -> IAH |        17 |                   70.59 |                   11.76 |                5.88 |               29.62 |                   204.03 |
| TVC -> PGD |        11 |                   81.82 |                   45.45 |                0    |               60.09 |                   203.32 |
| BOS -> RSW |       243 |                   36.63 |                   10.7  |                0.82 |               14.8  |                   201.36 |
| DEN -> MAF |       119 |                   42.02 |                   16.81 |                1.68 |               26.9  |                   201.17 |
| JFK -> PBI |       198 |                   37.88 |                   13.64 |                1.01 |               18.63 |                   200.51 |
| BOS -> TPA |       235 |                   36.6  |                    9.79 |                1.7  |               16.03 |                   199.98 |
| TVC -> DTW |        66 |                   46.97 |                   15.15 |                0    |               24.97 |                   197.49 |
| DTW -> MIA |       141 |                   39.72 |                   12.06 |                0    |               17.8  |                   196.85 |
| DFW -> BOI |        62 |                   46.77 |                   20.97 |                4.84 |               22.46 |                   193.77 |
| ROA -> SFB |        12 |                   75    |                   25    |                8.33 |               61.36 |                   192.37 |

## Interpretation

Airports with high disruption-risk scores are not simply delayed airports; they are airports where delay and cancellation performance interact with network centrality. These airports are important candidates for disruption simulation and recovery optimization in later stages of the project.

Routes with high route-delay-risk scores combine high delay rates with meaningful flight volume. These routes are useful for identifying where localized disruptions may create larger downstream effects.
