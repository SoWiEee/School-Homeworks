package 期末Q1;

public class Game {

	public static void main(String[] args) {
		Role R []=new Role [6];
		int level;
		level = (int)(Math.random()*10);
		R[0]= new Warrior("戰士1號",400,1000,level);
		level = (int)(Math.random()*10);
		R[1]=new Warrior ("戰士2號",400,1000,level);
		level = (int)(Math.random()*10);
		R[2]=new Warrior ("戰士3號",400,1000,level);
		level = (int)(Math.random()*10);
		R[3]=new Witch ("法師1號",600,2000,level);
		level = (int)(Math.random()*10);
		R[4]=new Witch ("法師2號",600,2000,level);
		level = (int)(Math.random()*10);
		R[5]=new Witch ("法師3號",600,2000,level);
		
		double chance;
		
		while(true) {
			Role R1=R[(int)(Math.random()*6)];
			Role R2=R[(int)(Math.random()*6)];
			while(R1==R2) {
				R2=R[(int)(Math.random()*6)];
			}
			if (R1 instanceof Warrior) {
				((Warrior)R1).NewMoon(R2);
			}
			else
			{
				((Witch)R1).SmallFire(R2);
			}
			if(R2.getLife()<=0) {
				R2.print_char();
				System.exit(0);
			}
			if(R1.getMagic()<=70) {
				chance=Math.random();
				System.out.printf("%s",R1.getName());
				if(chance<0.2) {
					R1.Drink(new BlueDrug("large"));
					System.out.printf("Drink Large BlueDrug\n");}
					else if(chance>0.2 && chance <=0.6){
						R1.Drink(new BlueDrug("medium"));
						System.out.printf("Drink Medium BlueDrug\n");
					}
					else if(chance>0.6 && chance <=0.9){
						R1.Drink(new BlueDrug("small"));
						System.out.printf("Drink Small BlueDrug\n");
					}
					else {
						System.out.printf("No BlueDrug!!\n");
					}
				}
			if(R2.getLife()<=100) {
				chance=Math.random();
				System.out.printf("%s",R2.getName());
				if(chance<0.2) {
					R2.Drink(new RedDrug("large"));
					System.out.printf("Drink Large BlueDrug\n");}
					else if(chance>0.2 && chance <=0.6){
						R2.Drink(new RedDrug("medium"));
						System.out.printf("Drink Medium BlueDrug\n");
					}
					else if(chance>0.6 && chance <=0.9){
						R2.Drink(new RedDrug("small"));
						System.out.printf("Drink Small BlueDrug\n");
					}
					else {
						System.out.printf("No RedDrug!!\n");
					}
				}
			}
		}

	}

