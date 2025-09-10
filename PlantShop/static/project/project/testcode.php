<?php
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Extract and sanitize inputs
    $nm = trim($_POST['nm'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $pwd = $_POST['pwd'] ?? '';
    $cpwd = $_POST['cpwd'] ?? '';
    $mno = trim($_POST['mno'] ?? '');

    $errors = [];

    // Validate name
    if (empty($nm)) {
        $errors[] = "Enter Full Name";
    }

    // Validate email
    if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors[] = "Enter valid Email";
    }

    // Validate password
    if (empty($pwd) || empty($cpwd)) {
        $errors[] = "Enter Password and Confirm Password";
    } elseif ($pwd !== $cpwd) {
        $errors[] = "Passwords do not match";
    } elseif (strlen($pwd) < 6) {
        $errors[] = "Password must be at least 6 characters";
    }

    // Validate mobile number
    if (empty($mno)) {
        $errors[] = "Enter Mobile Number";
    } elseif (!is_numeric($mno)) {
        $errors[] = "Mobile Number must be numeric";
    } elseif (strlen($mno) < 10) {
        $errors[] = "Mobile Number must be at least 10 digits";
    }

    // Check for errors
    if (!empty($errors)) {
        $_SESSION['error'] = $errors;
        header("Location: registration.php");
        exit();
    }

    // Connect to the database
    $con = mysqli_connect("localhost", "root", "", "project");

    if (!$con) {
        die("Database connection failed: " . mysqli_connect_error());
    }

    // Escape and hash
    $nm = mysqli_real_escape_string($con, $nm);
    $email = mysqli_real_escape_string($con, $email);
    $mno = mysqli_real_escape_string($con, $mno);
    $hashedPwd = password_hash($pwd, PASSWORD_BCRYPT);
    $time = time();

    $query = "INSERT INTO registration (reg_nm, reg_mno, reg_pwd, reg_email, reg_time)
              VALUES ('$nm', '$mno', '$hashedPwd', '$email', '$time')";

    if (mysqli_query($con, $query)) {
        $_SESSION['registration'] = "Registered Successfully";
    } else {
        $_SESSION['error'] = ["Registration Failed: " . mysqli_error($con)];
    }

    mysqli_close($con);
    header("Location: registration.php");
    exit();
} else {
    header("Location: registration.php");
    exit();
}
?>
