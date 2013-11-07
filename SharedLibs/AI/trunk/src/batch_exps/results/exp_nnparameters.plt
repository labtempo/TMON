reset

set terminal pngcairo size 1024,800 monochrome
set output "exp_nnparameters_linear.png"

f = 'exp_nnparameters_results_249.txt'

set xlabel "Janela de previsão"
set ylabel "Taxa de aprendizado"
set zlabel "RMSE"
#set zrange[0:6]

set grid
set dgrid3d 15,10
set style data lines
set view 120,240

#set samples 20, 20
#set isosamples 21, 21
#set contour surface
#set cntrparam levels auto 200
set pm3d at b
unset key

set format y "%1.0e"
set ytics offset -0.5,-.05
set xtics offset 0.5,.05
set logscale y

set cbrange[0:5]
set palette defined ( 0 "white", 5 "black" )

splot f u 1:2:3 index 1 t ""
