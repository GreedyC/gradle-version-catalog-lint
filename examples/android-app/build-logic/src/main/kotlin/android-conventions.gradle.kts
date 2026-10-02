val libs = versionCatalogs.named("libs")

dependencies {
    add("implementation", libs.findLibrary("androidx-core-ktx").get())
    add("implementation", libs.findLibrary("androidx-core-ktxx").get()) // typo -> fails at configuration time
}
