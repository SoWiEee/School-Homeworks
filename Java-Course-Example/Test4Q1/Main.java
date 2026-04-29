import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class Main extends JFrame implements ActionListener {

    static Main frm = new Main();   // window
    static Container cp = frm.getContentPane();     // 內容層

    static final JLabel lab_w = new JLabel("Weight (kg)");
    static final JLabel lab_h = new JLabel("Height (m)");
    static final JLabel lab_a = new JLabel("Age");
    static final JLabel lab_g = new JLabel("Gender");
    static JTextField txtf_w = new JTextField("Enter weight in kg");
    static JTextField txtf_h = new JTextField("Enter height in meters");
    static JTextArea result = new JTextArea("Result");
    static JButton btn = new JButton("Compute");
    static JButton exit = new JButton("Exit");
    static JRadioButton rb1 = new JRadioButton("Male");
    static JRadioButton rb2 = new JRadioButton("Female");
    static ButtonGroup grp = new ButtonGroup();
    static Choice ch = new Choice();

    public static void main(String[] args) {

        // layout
        frm.setTitle("BMI Calc");
        frm.setLayout(null);
        frm.setSize(400, 400);

        lab_h.setBounds(10, 10, 80, 30);
        lab_w.setBounds(10, 50, 80, 30);
        lab_a.setBounds(10, 90, 80, 30);
        lab_g.setBounds(10, 130, 80, 30);
        txtf_h.setBounds(100, 10, 200, 30);
        txtf_w.setBounds(100, 50, 200, 30);
        ch.setBounds(100, 90, 200, 30);
        rb1.setBounds(80, 130, 80, 30);
        rb2.setBounds(170, 130, 80, 30);
        btn.setBounds(10, 160, 100, 40);
        exit.setBounds(120, 160, 100, 40);
        result.setBounds(10, 200, 360, 150);
        result.setEditable(false);

        // listener
        btn.addActionListener(frm);
        exit.addActionListener(frm);

        // embed
        for(int i = 1; i <= 20; i++){
            ch.addItem("" + i);
        }

        grp.add(rb1);
        grp.add(rb2);
        cp.add(result);
        cp.add(lab_h);
        cp.add(lab_w);
        cp.add(lab_a);
        cp.add(lab_g);
        cp.add(txtf_w);
        cp.add(txtf_h);
        cp.add(ch);
        cp.add(rb1);
        cp.add(rb2);
        cp.add(btn);
        cp.add(exit);

        // end
        frm.setVisible(true);
        frm.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
    }

    // event handle
    public void actionPerformed(ActionEvent e) {
        JButton button = (JButton) e.getSource();   // btn or exit
        if (button == btn) {
            double w = Double.parseDouble(txtf_w.getText());
            double h = Double.parseDouble(txtf_h.getText());
            double BMI = w / (h*h);

            String weightString;
            if (BMI < 18.5) {
                weightString = "Under weight, Eat more!";
            } else if (18.5 <= BMI && BMI <= 23.9) {
                weightString = "Normal weight, Great!";
            } else if (24 <= BMI && BMI < 26.9) {
                weightString = "Over weight, Remember to do exercises!";
            } else {
                weightString = "Obesity, Go on diet, Now!";
            }
            result.setText("");     // clear
            result.append("BMI: " + BMI + "\n");
            result.append("[*] " + weightString + "\n");

            result.append(ch.getSelectedItem().toString() + "years, ");

            if(rb1.isSelected()) {
                result.append("Male");
            }else{
                result.append("Female");
            }
        }else if(button == exit){
            System.exit(0);
        }
    }
}
