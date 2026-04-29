import java.security.*;

public class Main {

    public static void main(String[] args) {
        SecureRandom randomNumber = new SecureRandom();

        Warrior warrior1 = new Warrior("Kirito1", 400, 100);
        Warrior warrior2 = new Warrior("Kirito2", 400, 100);

        Mage mage1 = new Mage("Gojo1", 280, 200);
        Mage mage2 = new Mage("Gojo2", 280, 200);

        Priest priest1 = new Priest("Priest1", 300, 200);
        Priest priest2 = new Priest("Priest2", 300, 200);

        Role[] roles = {warrior1, warrior2, mage1, mage2, priest1, priest2};

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

            for(Role r : roles) {
                if(r instanceof Warrior) r.setLife((int)((float)r.getLife() + ((Warrior) r).recoverLife()));
                else if(r instanceof Mage) r.setMagic((int)((float)r.getLife() + ((Mage) r).recoverMagic()));;
            }
        }
    }

    public static void printStatus(Role r1, Role r2) {
        System.out.println(r1);
        System.out.println(r2);
        System.out.println();
    }
}