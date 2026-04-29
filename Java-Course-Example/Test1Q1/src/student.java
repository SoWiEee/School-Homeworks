//store student's test grades
public class student {
	private int test[]=new int[3];//array to store three test grade
	
	public student(){//initial random grade
		test[0]=(int)(Math.random()*100)+1;
		test[1]=(int)(Math.random()*100)+1;
		test[2]=(int)(Math.random()*100)+1;
	}



	//get test i's grade
	public int get_test(int i) {
		return test[i];
	}
	//get three test grade's average
	public double get_average() {
		return (test[0]+test[1]+test[2])/3.0;
	}
}
