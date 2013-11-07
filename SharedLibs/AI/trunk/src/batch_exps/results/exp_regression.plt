reset

set terminal pngcairo size 1024,768

set output 'exp_regression_results.png'

file = 'exp_regression_results.txt'

set grid
set xlabel 'Janela de regressão (segundos)'
set ylabel 'RMSE'

set key top left

set xrange[0:1000]

plot \
file index 0 w lp t "Observations", \
file index 1 w lp t "Rolling Perceptron", \
file index 2 w lp t "Holt"

exit