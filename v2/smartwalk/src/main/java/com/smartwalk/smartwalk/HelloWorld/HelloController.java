package com.smartwalk.smartwalk.HelloWorld;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/test")
public class HelloController {

    //FOR TESTING PORPOUSES

    @GetMapping("/")
    public String index() {
        return "Greetings from Spring Boot!";
    }

    @PutMapping("/{id}")
    public String index2(@PathVariable Long id) {
        return "Greetings from Spring Boot! - " + id;
    }

}