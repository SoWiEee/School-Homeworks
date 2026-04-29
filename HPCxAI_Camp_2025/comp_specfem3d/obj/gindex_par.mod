V34 :0x24 gindex_par
16 gindex3D_par.f90 S624 0
07/25/2025  23:58:08
use shared_input_parameters public 0 indirect
use shared_compute_parameters public 0 indirect
use shared_parameters public 0 direct
use specfem_par public 0 direct
use specfem_par_crustmantle public 0 direct
use specfem_par_innercore public 0 direct
use specfem_par_outercore public 0 direct
use specfem_par_trinfinite public 0 direct
use specfem_par_infinite public 0 direct
use constants public 0 direct
use constants_solver public 0 indirect
use specfem_par_full_gravity public 0 direct
enduse
D 82 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 85 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 88 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 91 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 94 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 97 23 9 1 11 696 0 0 0 0 0
 0 696 11 11 696 696
D 104 23 10 1 11 697 0 0 0 0 0
 0 697 11 11 697 697
D 107 23 10 1 11 697 0 0 0 0 0
 0 697 11 11 697 697
D 2011 26 3824 776 3823 7
D 2047 22 7
D 2049 22 7
D 2051 22 7
D 2053 22 7
D 2055 22 7
S 624 24 0 0 0 9 1 0 5012 10005 8000 A 0 0 0 0 B 0 28 0 0 0 0 0 0 0 0 0 0 55 0 0 0 0 0 0 0 0 28 0 0 0 0 0 0 gindex_par
S 626 23 0 0 0 6 1304 624 5033 4 0 A 0 0 0 0 B 400000 30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 myrank
S 627 23 0 0 0 6 861 624 5040 4 0 A 0 0 0 0 B 400000 30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 ngllx
S 628 23 0 0 0 6 862 624 5046 4 0 A 0 0 0 0 B 400000 30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 nglly
S 629 23 0 0 0 6 863 624 5052 4 0 A 0 0 0 0 B 400000 30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 ngllz
S 631 23 0 0 0 6 1492 624 5076 4 0 A 0 0 0 0 B 400000 32 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 nproctot
S 798 3 0 0 0 7 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 6 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 7
S 799 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 -1 -1086541139 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 800 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 -1 -1076805840 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 801 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 -1 -1086413001 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 802 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 -1 -1078188647 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 803 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 -1 -1070327781 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 804 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1023858089 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 805 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1062387960 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 806 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1052989446 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 807 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1045226745 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 808 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1071381111 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 809 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1049247089 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 810 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1048532495 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 811 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1055854349 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 812 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1058340850 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 813 3 0 0 0 9 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 1062790546 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9
S 854 3 0 0 0 7 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 7
R 861 16 6 constants ngllx
R 862 16 7 constants nglly
R 863 16 8 constants ngllz
R 1202 7 347 constants alpha_lddrk$ac
R 1204 7 349 constants beta_lddrk$ac
R 1206 7 351 constants c_lddrk$ac
R 1280 7 425 constants pole_inf$ac
R 1304 6 449 constants myrank
R 1492 6 30 shared_compute_parameters nproctot
S 1737 3 0 0 0 7 1 1 0 0 0 A 0 0 0 0 B 0 0 0 0 0 0 0 0 0 17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 7
R 3823 25 1201 specfem_par_crustmantle kl_reg_grid_variables
R 3824 5 1202 specfem_par_crustmantle dlat kl_reg_grid_variables
R 3825 5 1203 specfem_par_crustmantle dlon kl_reg_grid_variables
R 3827 5 1205 specfem_par_crustmantle rlayer kl_reg_grid_variables
R 3828 5 1206 specfem_par_crustmantle rlayer$sd kl_reg_grid_variables
R 3829 5 1207 specfem_par_crustmantle rlayer$p kl_reg_grid_variables
R 3830 5 1208 specfem_par_crustmantle rlayer$o kl_reg_grid_variables
R 3832 5 1210 specfem_par_crustmantle nlayer kl_reg_grid_variables
R 3833 5 1211 specfem_par_crustmantle npts_total kl_reg_grid_variables
R 3835 5 1213 specfem_par_crustmantle ndoubling kl_reg_grid_variables
R 3836 5 1214 specfem_par_crustmantle ndoubling$sd kl_reg_grid_variables
R 3837 5 1215 specfem_par_crustmantle ndoubling$p kl_reg_grid_variables
R 3838 5 1216 specfem_par_crustmantle ndoubling$o kl_reg_grid_variables
R 3841 5 1219 specfem_par_crustmantle nlat kl_reg_grid_variables
R 3842 5 1220 specfem_par_crustmantle nlat$sd kl_reg_grid_variables
R 3843 5 1221 specfem_par_crustmantle nlat$p kl_reg_grid_variables
R 3844 5 1222 specfem_par_crustmantle nlat$o kl_reg_grid_variables
R 3847 5 1225 specfem_par_crustmantle nlon kl_reg_grid_variables
R 3848 5 1226 specfem_par_crustmantle nlon$sd kl_reg_grid_variables
R 3849 5 1227 specfem_par_crustmantle nlon$p kl_reg_grid_variables
R 3850 5 1228 specfem_par_crustmantle nlon$o kl_reg_grid_variables
R 3853 5 1231 specfem_par_crustmantle npts_before_layer kl_reg_grid_variables
R 3854 5 1232 specfem_par_crustmantle npts_before_layer$sd kl_reg_grid_variables
R 3855 5 1233 specfem_par_crustmantle npts_before_layer$p kl_reg_grid_variables
R 3856 5 1234 specfem_par_crustmantle npts_before_layer$o kl_reg_grid_variables
S 7111 6 4 0 0 6 7112 624 107856 4 0 A 0 0 0 0 B 0 49 0 0 0 0 0 0 0 0 0 0 7114 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 ignode_end
S 7112 6 4 0 0 6 7113 624 107867 4 0 A 0 0 0 0 B 0 51 0 0 0 4 0 0 0 0 0 0 7114 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 gnf_end
S 7113 6 4 0 0 6 1 624 107875 4 0 A 0 0 0 0 B 0 53 0 0 0 8 0 0 0 0 0 0 7114 0 0 0 0 0 0 0 0 0 0 624 0 0 0 0 gnf_end1
S 7114 11 0 0 0 9 7110 624 107884 40800000 805000 A 0 0 0 0 B 0 55 0 0 0 12 0 0 7111 7113 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 _gindex_par$0
A 145 2 0 0 0 10 617 0 0 0 145 0 0 0 0 0 0 0 0 0 0 0
A 218 2 0 0 0 9 613 0 0 0 218 0 0 0 0 0 0 0 0 0 0 0
A 523 2 0 0 0 9 799 0 0 0 523 0 0 0 0 0 0 0 0 0 0 0
A 524 2 0 0 0 9 800 0 0 0 524 0 0 0 0 0 0 0 0 0 0 0
A 525 2 0 0 0 9 801 0 0 0 525 0 0 0 0 0 0 0 0 0 0 0
A 526 2 0 0 0 9 802 0 0 0 526 0 0 0 0 0 0 0 0 0 0 0
A 527 2 0 0 0 9 803 0 0 0 527 0 0 0 0 0 0 0 0 0 0 0
A 535 2 0 0 0 9 804 0 0 0 535 0 0 0 0 0 0 0 0 0 0 0
A 536 2 0 0 0 9 805 0 0 0 536 0 0 0 0 0 0 0 0 0 0 0
A 537 2 0 0 0 9 806 0 0 0 537 0 0 0 0 0 0 0 0 0 0 0
A 538 2 0 0 0 9 807 0 0 0 538 0 0 0 0 0 0 0 0 0 0 0
A 539 2 0 0 0 9 808 0 0 0 539 0 0 0 0 0 0 0 0 0 0 0
A 540 2 0 0 0 9 809 0 0 0 540 0 0 0 0 0 0 0 0 0 0 0
A 548 2 0 0 0 9 810 0 0 0 548 0 0 0 0 0 0 0 0 0 0 0
A 549 2 0 0 0 9 811 0 0 0 549 0 0 0 0 0 0 0 0 0 0 0
A 550 2 0 0 0 9 812 0 0 0 550 0 0 0 0 0 0 0 0 0 0 0
A 551 2 0 0 0 9 813 0 0 0 551 0 0 0 0 0 0 0 0 0 0 0
A 696 2 0 0 0 7 798 0 0 0 696 0 0 0 0 0 0 0 0 0 0 0
A 697 2 0 0 0 7 854 0 0 0 697 0 0 0 0 0 0 0 0 0 0 0
A 705 1 0 1 0 82 1202 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
A 713 1 0 1 93 88 1204 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
A 721 1 0 1 0 94 1206 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
A 726 1 0 3 0 104 1280 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
A 813 2 0 0 0 7 1737 0 0 0 813 0 0 0 0 0 0 0 0 0 0 0
Z
J 1187 1 1
V 705 82 7 0
R 0 85 0 0
A 0 9 0 0 1 218 1
A 0 9 0 0 1 523 1
A 0 9 0 0 1 524 1
A 0 9 0 0 1 525 1
A 0 9 0 0 1 526 1
A 0 9 0 0 1 527 0
J 1191 1 1
V 713 88 7 0
R 0 91 0 0
A 0 9 0 0 1 535 1
A 0 9 0 0 1 536 1
A 0 9 0 0 1 537 1
A 0 9 0 0 1 538 1
A 0 9 0 0 1 539 1
A 0 9 0 0 1 540 0
J 1195 1 1
V 721 94 7 0
R 0 97 0 0
A 0 9 0 0 1 218 1
A 0 9 0 0 1 535 1
A 0 9 0 0 1 548 1
A 0 9 0 0 1 549 1
A 0 9 0 0 1 550 1
A 0 9 0 0 1 551 0
J 1388 1 1
V 726 104 7 0
R 0 107 0 0
A 0 10 0 0 1 145 1
A 0 10 0 0 1 145 1
A 0 10 0 0 1 145 0
T 3823 2011 0 0 0 0
A 3829 7 2047 0 1 2 1
A 3828 7 0 813 1 10 1
A 3837 7 2049 0 1 2 1
A 3836 7 0 813 1 10 1
A 3843 7 2051 0 1 2 1
A 3842 7 0 813 1 10 1
A 3849 7 2053 0 1 2 1
A 3848 7 0 813 1 10 1
A 3855 7 2055 0 1 2 1
A 3854 7 0 813 1 10 0
Z
