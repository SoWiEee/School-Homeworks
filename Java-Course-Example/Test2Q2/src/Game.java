public class Game {

	public static void main(String[] args) {
		
		Role R []=new Role[6];
		
		int level;//6個人
		level=(int)(Math.random()*10);
		R[0]=new Warrior("戰士1號",400,1000,level);
		level=(int)(Math.random()*10);
		R[1]=new Warrior("戰士2號",400,1000,level);
		level=(int)(Math.random()*10);
		R[2]=new Warrior("戰士3號",400,1000,level);
		level=(int)(Math.random()*10);
		R[3]=new Witch("法師1號",280,2000,level);
		level=(int)(Math.random()*10);
		R[4]=new Witch("法師2號",280,2000,level);
		level=(int)(Math.random()*10);
		R[5]=new Witch("法師3號",280,2000,level);
		
		double chance;//喝藥機率
		
		while(true) {
			//每次2個人
			Role R1= R[(int)(Math.random()*6)];
			Role R2= R[(int)(Math.random()*6)];
			
			while(R1==R2) {//確保不同人攻擊、被攻擊
				R2=R[(int)(Math.random()*6)];
			}
			
			if(R1 instanceof Warrior) {//攻擊方式
				((Warrior)R1).NewMoon(R2);
			}
			else {
				((Witch)R1).SmallFire(R2);
			}
			
			if(R2.getLife()<=0) {//死亡
				R2.print_char();
				System.exit(0);//結束程式!
			}
			
			if(R1.getMagic()<70) {//補魔，攻擊者才補魔
				chance = Math.random();
				System.out.printf("%s",R1.getName());
				if(chance<=0.2)
				{
					R1.Drink(new BlueDrug("large"));
					System.out.println("Drink LARGE BlueDrug\n");
				}
				else if(chance>0.2 && chance <= 0.6)
				{
					R1.Drink(new BlueDrug("medium"));
					System.out.println("Drink MEDIUM BlueDrug\n");
				}
				else if(chance>0.6 && chance <=0.9)
				{	
					R1.Drink(new BlueDrug("small"));
					System.out.println("Drink Small BlueDrug\n");
				}
				else
					System.out.println("No BlueDrug!!\n");
			}
			if(R2.getLife()<100)//補血，被攻擊者才補血
			{
				chance=Math.random();
				System.out.printf("%s",R2.getName());
				if(chance <= 0.2)
				{
					R2.Drink(new RedDrug("large"));
					System.out.printf("Drink LARGE RedDrug\n");
				}
				else if(chance > 0.2 && chance <= 0.6)
				{
					R2.Drink(new RedDrug("medium"));
					System.out.printf("Drink MEDIUM RedDrug\n");
				}
				else if(chance > 0.6 && chance <= 0.9)
				{
					R2.Drink(new RedDrug("small"));
					System.out.printf("Drink SMALL RedDrug\n");
				}
				else
					System.out.println("No RedDrug!!\n");
			}
		}
	}
}
