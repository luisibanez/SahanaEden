// User extensions can be added here.
//
// Keep this file to avoid  mystifying "Invalid Character" error in IE

Selenium.prototype.doTypeRandom = function(locator, length) {
    // All locator-strategies are automatically handled by "findElement"
    var element = this.page().findElement(locator);

    // Create the random string
    var keylist="abcdefghijklmnopqrstuvwxyz123456789"
    var temp=''

    function randomstring(length){
        temp=''
        for (i=0;i<length;i++)
            temp+=keylist.charAt(Math.floor(Math.random()*keylist.length))
        return temp
    }
    
    var valueToType = randomstring(length);

    // Replace the element text with the new text
    this.page().replaceText(element, valueToType);
};


Selenium.prototype.doStoreRandom = function(length, variableName) {
    // Create the random string
    var keylist="abcdefghijklmnopqrstuvwxyz123456789"
    var temp=''

    function randomstring(length){
        temp=''
        for (i=0;i<length;i++)
            temp+=keylist.charAt(Math.floor(Math.random()*keylist.length))
        return temp
    }
    
    var expression = randomstring(length);

    // Replace the element text with the new text
    storedVars[variableName] = expression;
    
};