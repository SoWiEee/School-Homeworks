import java.security.SecureRandom;

public class Main {
    public static void main(String[] args) {
        Role[] roles = new Role[6];
        roles[0] = new Witch("Witch_A", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "cloak1");
        roles[1] = new Witch("Witch_B", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "cloak2");
        roles[2] = new Witch("Witch_C", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "cloak3");
        roles[3] = new Warrior("Warrior_A", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "armor1");
        roles[4] = new Warrior("Warrior_B", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "armor2");
        roles[5] = new Warrior("Warrior_C", Personate.BASELIFE+180, Personate.BASEMAGIC+1500, "armor3");

        SecureRandom random = new SecureRandom();
        int m, n, chance;

        // game start
        while(true) {
            do{
                m = random.nextInt(6);  // 0~5
                n = random.nextInt(6);
            }while(m == n);

            // m attack n
            System.out.println(roles[m].getName() + " attacked " + roles[n].getName() + "...");
            if(roles[m] instanceof Witch) { ((Witch) roles[m]).SmallFire(roles[n]); }
            if(roles[m] instanceof Warrior) { ((Warrior) roles[m]).NewMoon(roles[n]); }

            // dead
            if(roles[n].getLife() <= 0){
                roles[n].print_char();
                break;
            }

            // drink drug
            if(roles[m].getMagic() < 70) {
                chance = random.nextInt(10)+1;  // 1~10
                if(chance == 1){
                    roles[m].Drink(new BlueDrug("Large"));
                    System.out.println("[*] "+ roles[m].getName() +" drink Large BlueDrug\n");
                }else if(chance <= 4){
                    roles[m].Drink(new BlueDrug("Medium"));
                    System.out.println("[*] "+ roles[m].getName() +" drink Medium BlueDrug\n");
                }else if(chance <= 8){
                    roles[m].Drink(new BlueDrug("Small"));
                    System.out.println("[*] "+ roles[m].getName() +" drink Small BlueDrug\n");
                }
            }
            if(roles[n].getLife() < 70) {
                chance = random.nextInt(10)+1;  // 1~10
                if(chance == 1){
                    roles[n].Drink(new RedDrug("Large"));
                    System.out.println("[*] "+ roles[n].getName() +" drink Large RedDrug\n");
                }else if(chance <= 4){
                    roles[n].Drink(new RedDrug("Medium"));
                    System.out.println("[*] "+ roles[n].getName() +" drink Medium RedDrug\n");
                }else if(chance <= 8){
                    roles[n].Drink(new RedDrug("Small"));
                    System.out.println("[*] "+ roles[n].getName() +" drink Small RedDrug\n");
                }
            }
        }
    }
}