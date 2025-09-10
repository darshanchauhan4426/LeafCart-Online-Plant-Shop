<?php 

include("inc/header.php");

?>



<!-- ##### Breadcrumb Area Start ##### -->
<div class="breadcrumb-area">
    <!-- Top Breadcrumb Area -->
    <div class="top-breadcrumb-area bg-img bg-overlay d-flex align-items-center justify-content-center" style="background-image: url(img/bg-img/24.jpg);">
        <h2>Contact US</h2>
    </div>

    <div class="container">
        <div class="row">
            <div class="col-12">
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="#"><i class="fa fa-home"></i> Home</a></li>
                        <li class="breadcrumb-item active" aria-current="page">Contact</li>
                    </ol>
                </nav>
            </div>
        </div>
    </div>
</div>
<!-- ##### Breadcrumb Area End ##### -->



<!-- ##### Registartion Area Start ##### -->
<section class="contact-area">
    <div class="container">
        <div class="row align-items-center justify-content-between">
            <div class="col-12 col-lg-5">
                
                <!-- Registration Form Area -->
                <div class="contact-form-area mb-100">
                    <form action="registration_process.php" method="post">
                        <div class="row">
                            <div class="col-12">
                                <div class="form-group">
                                <?php                            
                                    if(isset($_SESSION['msg'])){
                                        echo $_SESSION['msg'];
                                        echo'<br>';
                                        unset($_SESSION['msg']);
                                    }                               
                                ?>
                                <label for="nm">Full Name</label>
                                    <input type="text" name="nm" class="form-control" id="nm" placeholder="Your Name" >
                                    <?php 
                                    if(isset($_SESSION['error']['nm'])){
                                    ?>

                                    <div style="color:light-red;"><?php echo $_SESSION['error']['nm'];?></div>
                                    
                                    <?php 
                                    unset($_SESSION['error']['nm']);
                                    }?>
                                </div>

                            </div>

                            <div class="col-12">
                                <div class="form-group">
                                <label for="email">Email</label>
                                    <input type="email" name="email" class="form-control" id="email" placeholder="Your Email">
                                </div>
                            </div>

                            <div class="col-12">
                                <div class="form-group">
                                <label for="pwd">Password</label>
                                    <input type="text" name="pwd" class="form-control" id="pwd" placeholder="Your Password">
                                </div>
                            </div>

                            <div class="col-12">
                                <div class="form-group">
                                <label for="cpwd">Confirm Password</label>
                                    <input type="text" name="cpwd" class="form-control" id="cpwd" placeholder="Confirm Your Password">
                                </div>
                            </div>

                            <div class="col-12">
                                <div class="form-group">
                                <label for="mno">Mobile Number</label>
                                    <input type="text" name="mno" class="form-control" id="mno" placeholder="Your Mobile Number">
                                </div>
                            </div>
                            
                            <div class="col-12">
                                <button type="submit" class="btn alazea-btn mt-15">Register</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</section>
<!-- ##### Registration Area End ##### -->

<?php

include("inc/footer.php");

?>