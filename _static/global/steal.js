let stealComponent = {
    components: {
      'property-component': propertyComponent
    },
    props: { properties: Array},
    data: function () {
        return {
          playerId: Number,
          locationx: 0,
          locationy: 0,
        }
    },
    mounted: function() {
      let that = this;
      Draggable.create("#location", {
        minimumMovement: 1,
        bounds: document.getElementById("steal-container"), //todo add ref stuff
        snap: function(val) {
        },
        onDragEnd: function() {
          that.checkLocation(this)
        },
      });
    },
    methods: {
      checkLocation: function(that) {
        if(that.hitTest(this.$refs.htarget, '100%')){
          //location-center
          if(that.hitTest(this.$refs.prop1, '1%')) {
              let property = document.getElementById('prop1').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop2, '1%')) {
              let property = document.getElementById('prop2').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop3, '1%')) {
              let property = document.getElementById('prop3').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop4, '1%')) {
              let property = document.getElementById('prop4').getBoundingClientRect()
              this.calculateLocation(property);
          } else {
              gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref 
          }
          
        } else{
          gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref 
        }
      },
      calculateLocation(property) {
        gsap.to('#locationrect', {fill: 'red'})
        let location = this.$refs.location.getBoundingClientRect()
        this.locationx = location.x - property.x + .25
        this.locationy = location.y - property.y + .25 //todo add variable radius here palio
      }
    },
    template: `
      <div id="steal-container">
        <div ref='htarget' class="property-container">
          <div v-for="property in properties" class='property' v-bind:player-id="property" :id='"prop" + property' :ref='"prop" + property'>{{property}}</div>
  
        </div>
        <div class="location-start">
          <div>
            drag location<br>
            x: {{locationx}}<br> 
            y: {{locationy}}<br>
          </div>
          <svg id="location" height="21" width="21">
            <rect id="locationrect" x="0" y="0" width="21" height="21" style="fill:green;stroke:black;stroke-width:1;fill-opacity:0.1;stroke-opacity:0.9" />
            
            <circle ref="location" cx="10" cy="10" r=".5" fill="black" />
            Sorry, your browser does not support inline SVG.  
          </svg> 
        </div>
      </div>
    `
  }
  
  let stealGameComponent = {
    components: {
      'steal-component': stealComponent,
  
    },
    props: {
      properties: Array,
      playerGroupId: String,
  
    },
    data: function() {
      return {
        playerId: Number
      }
    },
    template: 
      `
      <div class="steal" style="display:flex; flex-wrap: wrap">
        <div class="game">
            <div class="">
                <steal-component :properties="properties"></steal-component>
            </div>
        </div>
      </div>
      `
  }