reset

set terminal pngcairo size 1024,768 monochrome dashed

set output 'exp_metrics_notice_errors_SPIRIT.png'

metrics = 'exp_metrics_results_all.txt'

set grid
set xlabel 'Janela de previsão (minutos)'
set ylabel 'RMSE (segundos)'
set xrange [0:15]
set yrange [0:600]
set xtics 1,1,15
set style data lp

set key top left

plot \
metrics index 5 u 1:6 t 'Naïve', \
metrics index 6 u 1:6 t 'Rolling Perceptron', \
metrics index 7 u 1:6 t 'Linear Perceptron', \
metrics index 8 u 1:6 t 'Adaptable Holt', \
metrics index 9 u 1:6 t 'Adaptable AR', \

unset output