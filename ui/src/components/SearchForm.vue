
<script setup>
</script>

<template>
  <main class=" px-4 md:px-0 pt-8">
    <div class="max-w-8xl mx-auto bg-slate-50 py-8 rounded-lg  px-4 md:px-0">
      <div
        class="absolute inset-x-0 top-[-10rem] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[-20rem]"
        aria-hidden="true"
      >
        <!-- <div
          class="relative left-1/2 -z-10 aspect-[1155/678] w-[36.125rem] max-w-none -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-40rem)] sm:w-[72.1875rem]"
          style="
            clip-path: polygon(
              74.1% 44.1%,
              100% 61.6%,
              97.5% 26.9%,
              85.5% 0.1%,
              80.7% 2%,
              72.5% 32.5%,
              60.2% 62.4%,
              52.4% 68.1%,
              47.5% 58.3%,
              45.2% 34.5%,
              27.5% 76.7%,
              0.1% 64.9%,
              17.9% 100%,
              27.6% 76.8%,
              76.1% 97.7%,
              74.1% 44.1%
            );
          "
        ></div> -->
      </div>
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-lg font-bold tracking-tight text-gray-900 sm:text-xl">Search for Expressions</h2>
        <!-- <p class="mt-2 text-lg leading-8 text-gray-600">
          This project investigates how they contributed to shaping disease concepts, illness
          experience, and medical practices throughout the 20th century.
        </p> -->
      </div>
      <form @submit.prevent="" class="mx-auto mt-8 max-w-xl  bg-slate-50">
        <div class="grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label for="search" class="block text-sm font-semibold leading-6 text-gray-900">Search for: </label>
            <input
              type="text"
              id="search"
              autocomplete="given-name"
              class="block w-full rounded-md border-0 px-3.5 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-sky-600 sm:text-sm sm:leading-6"
              placeholder="start typing :)"
            />
          </div>

        </div>

          <div class="my-4 block w-full">
             <p class="text-sm font-semibold leading-6 text-gray-900">Filter by:

                 <a class="text-xs text-gray-100 bg-rose-400 py-1 px-2 mr-1 rounded-lg items-center hover:cursor-pointer">
                    beautiful
                    <span  class="bg-rose-500 py-[0.5] px-1 rounded-full ">x</span>
                </a>
                 <a class="text-xs text-gray-100 bg-rose-400 py-1 px-2 mr-1 rounded-lg items-center hover:cursor-pointer">
                    profound
                    <span  class="bg-rose-500 py-[0.5] px-1 rounded-full ">x</span>
                </a>
            </p>
          </div>     

        <div class="mt-8">
          <a
            class="block w-full rounded-md bg-sky-600 px-4 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-sky-500 hover:cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
          >
            Search 
          </a>
        </div>
        <div class="mt-2">
          <a
            class="block w-full rounded-md bg-pink-600 px-4 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-pink-500 hover:cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-600"
          >
            Reset
          </a>
        </div>
      </form>
    </div>
  </main>
</template>