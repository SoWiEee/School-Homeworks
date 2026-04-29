import java.security.*;

public class Main {

    public static void main(String[] args) {
        SecureRandom randomNumber = new SecureRandom();

        Warrior warrior1 = new Warrior("Kirito1", 400, 100);
        Warrior warrior2 = new Warrior("Kirito2", 400, 100);
        Warrior warrior3 = new Warrior("Kirito3", 400, 100);

        Mage mage1 = new Mage("Gojo1", 280, 200);
        Mage mage2 = new Mage("Gojo2", 280, 200);
        Mage mage3 = new Mage("Gojo3", 280, 200);

        Role[] roles = {warrior1, warrior2, warrior3, mage1, mage2, mage3};

        for(Role r : roles) { System.out.println(r); }
        System.out.println();

        while(true) {
            int w = randomNumber.nextInt(6);
            int m = randomNumber.nextInt(6);
            if(w == m) continue;

            System.out.println(roles[w].getName() + " attacked " + roles[m].getName() + "...");
            if(roles[w] instanceof Warrior) ((Warrior)roles[w]).NewMoon(roles[m]);
            else if(roles[w] instanceof Mage) ((Mage)roles[w]).SmallFire(roles[m]);
            printStatus(roles[w], roles[m]);
        }
    }

    public static void printStatus(Role r1, Role r2) {
        System.out.println(r1);
        System.out.println(r2);
        System.out.println();
    }
}