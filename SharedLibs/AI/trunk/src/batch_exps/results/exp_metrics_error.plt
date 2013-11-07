reset

set terminal pngcairo size 1024,768 monochrome dashed

set output 'exp_metrics_error.png'

metrics = 'exp_metrics_results.txt'

set grid
set xlabel 'Janela de previsão (minutos)'
set ylabel 'RMSE (ºC)'
set style data lp

set key top left

plot \
metrics index 0 u 1:2 t 'Naïve', \
metrics index 1 u 1:2 t 'Rolling Perceptron', \
metrics index 2 u 1:2 t 'Linear Perceptron', \
metrics index 3 u 1:2 t 'AdaptableHolt', \
metrics index 4 u 1:2 t 'AdaptableAR', \

exit