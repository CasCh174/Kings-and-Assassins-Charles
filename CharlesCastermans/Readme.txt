Le fichier se lance facilement gr�ce � 'KingandAssassins.bat'.

Les modifictions apport�es au programme se trouvent toutes dans la classe 'class KingAndAssassinsClient(game.GameClient):'.

Les nouvelles fonctions sont:

-strat_roi (contient la strat�gie de d�placement de l'�quipe du roi)
-deplacement_groupe (permet de d�placer le roi en gardant toujours 3 chevaliers en guise de protection)
-ref_roi (permet de connaitre soit le pion qui se trouve � un certain endroit par rapport au roi, soit 
	  le d�placement d'un pion � un certain endroit par rapport au roi)
-pos_roi (permet de r�cup�rer la position du roi)
-strat_ass (contient la strat�gie de d�placement de l'�quipe des assassins)
-pos_vill (permet de r�cup�rer la postion du pion le plus proche d'une certaine position)
-distance (permet de caluler la distance entre deux cases)