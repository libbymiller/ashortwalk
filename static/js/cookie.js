function getUser(){

          let x = document.cookie;
          console.log("cookie",x);
          let y = x.split(";");
          console.log("cookie y",y);
          let person = null;
          if(y[0]!=null){
             let z = y[0].split("=");
             if(z[0]=="username"){
               person = z[1];
             }
          }
          console.log("person",person);
  return person;
}
