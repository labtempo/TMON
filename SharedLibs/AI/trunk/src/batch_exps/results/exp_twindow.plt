reset

set terminal pngcairo size 1024,800 monochrome
set output "exp_twindow_holt.png"

f = 'exp_twindow_results.txt'

set xlabel "Janela de treinamento"
set ylabel "Janela de previsão"
set zlabel "RMSE"

set grid
set dgrid3d 10,20
set style data lines
set pm3d at b
set view 60,325
unset key
#set contour base
set xrange[1:20]
set cbrange[0:2.5]
set palette defined ( 0 "white", 5 "black" )

splot f u 1:2:3 index 1 w l t ""
