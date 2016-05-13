Le fichier se lance facilement grâce à 'KingandAssassins.bat'.

Les modifictions apportées au programme se trouvent toutes dans la classe 'class KingAndAssassinsClient(game.GameClient):'.

Les nouvelles fonctions sont:

-strat_roi (contient la stratégie de déplacement de l'équipe du roi)
-deplacement_groupe (permet de déplacer le roi en gardant toujours 3 chevaliers en guise de protection)
-ref_roi (permet de connaitre soit le pion qui se trouve à un certain endroit par rapport au roi, soit 
	  le déplacement d'un pion à un certain endroit par rapport au roi)
-pos_roi (permet de récupérer la position du roi)
-strat_ass (contient la stratégie de déplacement de l'équipe des assassins)
-pos_vill (permet de récupérer la postion du pion le plus proche d'une certaine position)
-distance (permet de caluler la distance entre deux cases)