<?php 

session_start();

if(! empty($_POST))
{
    extract($_POST);

    $_SESSION['error'] = array();

    $error = array();

    if(empty($nm)){
        $_SESSION['error']['nm'] = "*Enter Your Full Name";
    }

    if(empty($email)){
        $error[] = "Enter Email";
    }

    if(empty($pwd) || empty($pwd)){
        $error[] = "Enter Password";
    }

    elseif($pwd != $cpwd){
        $error[] ="Enter Correct Password";
    }

    elseif(strlen($pwd) < 6){
        $error[] ="Enter 6 Digit Password";
    }

    if(empty($mno)){
        $error[] ="Enter Mobile number";
    }

    elseif(strlen($mno) < 10){
        $error[] ="Enter Minimum 10 Digit";
    }

    elseif(!is_numeric($mno)){
        $error[] = "Enter Numeric Number";
    }

    if(!empty($_SESSION["error"])){
        header("location:registration.php");
    }

    else{

        $con = mysqli_connect("localhost","root","");

        mysqli_select_db($con,"project");

        $t = time();

        $q = "insert into registration
            (reg_nm,reg_mno,reg_pwd,reg_email,reg_time)
            values ('".$nm."','".$mno."','".$pwd."','".$email."','".$t."')";

        mysqli_query($con, $q);

        $_SESSION['msg'] = "Registered Successfully !";

        header("location:registration.php");


    }
}

else{
    header("location:registration.php");
}

?>