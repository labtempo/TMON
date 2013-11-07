reset

set terminal pngcairo size 1024,768 monochrome dashed

set output 'exp_metrics_notice_errors_lateness.png'

metrics = 'exp_metrics_results.txt'

set grid
set xlabel 'Janela de previsão (minutos)'
set ylabel 'RMSE (segundos)'
set xrange [0:11]
set xtics 1,1,10
set style data lp

set key top right

plot \
metrics index 0 u 1:5 t 'Naïve', \
metrics index 1 u 1:5 t 'Rolling Perceptron', \
metrics index 2 u 1:5 t 'Linear Perceptron', \
metrics index 3 u 1:5 t 'Adaptable Holt', \
metrics index 4 u 1:5 t 'Adaptable AR', \

exit