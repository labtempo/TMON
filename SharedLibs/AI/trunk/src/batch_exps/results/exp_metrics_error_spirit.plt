reset

set terminal pngcairo size 1024,768

set output 'exp_metrics_error_spirit.png'

metrics = 'exp_metrics_results_249.txt'

set grid
set xlabel 'Janela de previsão (minutos)'
set ylabel 'RMSE'

set key top left

plot \
metrics index 5 u 1:2 w l t 'SPIRIT + Naïve', \
metrics index 6 u 1:2 w l t 'SPIRIT + Rolling Perceptron', \
metrics index 8 u 1:2 w l t 'SPIRIT + AdaptableHolt', \
metrics index 9 u 1:2 w l t 'SPIRIT + AdaptableAR', \

exit