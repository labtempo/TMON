reset

set terminal pngcairo size 1024,768 monochrome dashed

set output 'exp_metrics_notice_errors_combined.png'

metrics = 'exp_metrics_results_249.txt'

set grid
set xlabel 'Janela de previsão (minutos)'
set ylabel 'RMSE (segundos)'
set xrange [0:11]
set xtics 1,1,10
set style data lp

set key top left

plot \
metrics index 0 u 1:6 t 'Naïve', \
metrics index 1 u 1:6 t 'Rolling Perceptron', \
metrics index 2 u 1:6 t 'Linear Perceptron', \
metrics index 3 u 1:6 t 'Adaptable Holt', \
metrics index 4 u 1:6 t 'Adaptable AR', \
metrics index 0 u 1:6:($6 - ($6 - $4)/1):($6 + ($5 - $6)/1) w yerrorbars t '', \

exit