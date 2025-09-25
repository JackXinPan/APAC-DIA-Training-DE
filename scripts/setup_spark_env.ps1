# setup_spark_env.ps1
$env:SPARK_HOME = "C:\spark"
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
$env:PATH += ";$env:SPARK_HOME\bin;$env:JAVA_HOME\bin"
