
public class Warrior extends Role implements Jumpable {
	//默認構造函數
	public Warrior() {
		
	}
	//構造函數初始化
public Warrior(String name,int life, int magic,int level) {
	super(name,life,magic,level);
}

private String Armor = "Armor";

public void NewMoon(Role R) {//攻擊方式
	if(getMagic()>=10) {//如果攻擊者魔力10以上才攻擊
		int damage;
		
		if(R instanceof Warrior) {
			damage=25;//打戰士25
		}
		else {
			damage=40;//打巫師40
		}
		
		System.out.printf("%s 攻擊了 %s\n",getName(),R.getName());
		setMagic(getMagic()-10);//攻擊者減魔
		R.setLife(R.getLife()-damage);//被攻擊者減血
	}
	else {
		System.out.printf("%s 魔力不足\n",getName());
	}
	
	if(R.getLife()<=0) {
		System.out.printf("%s 被 %s 打死了\n",R.getName(),getName());
	}
}

@Override
public void Drink(Drug D) {
	if(D instanceof RedDrug) {
		setLife(getLife()+((RedDrug)D).getAddLife());
	}
	else {
		setMagic(getMagic()+((BlueDrug)D).getAddMagic());
	}
}

@Override
public void print_char() {
	System.out.printf("名稱:%s,血量:%s,魔力:%s,等級:%s",getName(),getLife(),getMagic(),getLevel());
}
}
