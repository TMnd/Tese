package com.smartwalk.smartwalk.errorHandling;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class RestExceptionHandler {
    // add exception handling code
    
    //Add an exception handler using @ExceptionHandler
    @ExceptionHandler
    public ResponseEntity<ErrorResponse> handleException(NotFoundException exc){

        //create a ErrorResponse
        ErrorResponse error = new ErrorResponse();
        error.setStatus(HttpStatus.NOT_FOUND.value());
        error.setMessage(exc.getMessage());
        error.setTimeStamp(System.currentTimeMillis());

        //return reponse entity
        return new ResponseEntity<>(error,HttpStatus.NOT_FOUND);
    }

    //add another exception handler ... to catch any exception (catch all)

    @ExceptionHandler
    public ResponseEntity<ErrorResponse> handleException(Exception exc){

        //create a ErrorResponse
        ErrorResponse error = new ErrorResponse();
        error.setStatus(HttpStatus.BAD_REQUEST.value());
        error.setMessage(exc.getMessage());
        error.setTimeStamp(System.currentTimeMillis());

        //return reponse entity
        return new ResponseEntity<>(error,HttpStatus.BAD_REQUEST);
    }
}
