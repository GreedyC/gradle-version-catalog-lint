plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.bundles.networking)
    implementation(libs.timber)
    // implementation(libs.androidx.appcompat)  <- commented out, does not count as usage
    implementation("com.squareup.retrofit2:retrofit:2.9.0") // hard-coded!
    testImplementation(libs.junit)
}
