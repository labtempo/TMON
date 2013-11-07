reset

set terminal wxt 0

#set cntrparam levels 1000000
set palette defined (0 'black', 1 'white')
set contour base
unset sur
set view map
#set iso 10000
#set samp 10000
unset key
set dgrid3d
set logscale y
set zrange[0:6]
set pm3d at b
set format y "%1.0e"
set xlabel "Janela de previsão"
set ylabel "Taxa de aprendizado"

f = 'exp_nnparameters_results_249.txt'

splot f u 1:2:3 index 0 t ""