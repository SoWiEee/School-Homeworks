import java.security.SecureRandom;

public class Main {
	
	private static final int RoleNUM = 6;
	private static int Round = 1;
	private static final Role[] wRoles = new Role[RoleNUM];
	
	public static void main(String[] args) {
		// random
		SecureRandom random = new SecureRandom();
		int m, n;
		
		// init role
		wRoles[0] = new Warrior("A", "Big Armor");
		wRoles[1] = new Warrior("B", "Bloodred Armor");
		wRoles[2] = new Warrior("C", "King Armor");
		wRoles[3] = new Witch("D", "White Cloak");
		wRoles[4] = new Witch("E", "Magic Cloak");
		wRoles[5] = new Witch("F", "Reflected Cloak");

		
		do{
			do{
				m = random.nextInt(RoleNUM);	// 0~5
				n = random.nextInt(RoleNUM);	// 0~5
			}while(m == n);

			Role attacker =  wRoles[m];
			System.out.println("Round " + (Round++) + ": " + attacker.getName() + " attack " + wRoles[n].getName());
			System.out.println("------------------------------");

			// attack
			attacker.attack_method(wRoles[n]);
			
			printinfo();

		}while(!isRoleDeath());
	}

	public static boolean isRoleDeath(){
		for(int i = 0 ; i < RoleNUM; i++){
			if(wRoles[i].getLife() <= 0){
				return true;
			}
		}
		return false;
	}

	public static void printinfo(){
		for(int i = 0 ; i < RoleNUM; i++){
			wRoles[i].print_char(); 
		}
	}
}