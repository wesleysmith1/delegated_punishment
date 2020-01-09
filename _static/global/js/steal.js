
  let stealGameComponent = {
    components: {
      'property-component': propertyComponent
    },
    props: {
      properties: Array,
      playerGroupId: String,
      playerLocation: Object,
    },
    data: function () {
        return {
            location: null,
          locationx: 0,
          locationy: 0,
            stealNotification: 'steal notification placeholder',
        }
    },
    mounted: function() {
        // this.location = this.$refs.location todo: implement ref for location and all properties retreived by id
      let that = this;
      let selector = '#location'
      Draggable.create(selector, {
        minimumMovement: 1,
        bounds: document.getElementById("steal-container"), //todo add ref stuff
        snap: function(val) {
        },
        onDragEnd: function() {
          that.checkLocation(this)
        },
      });
      // animate to start
      //   if (this.playerLocation && this.playerLocation.property !== null) {
      //     this.calculateLocation(property, 2);
      //
      //       let propertySelector = 'prop' + this.playerLocation.property
      //       let property = document.getElementById(propertySelector).getBoundingClientRect() //todo use refs
      //       let location = this.$refs.location.getBoundingClientRect()
      //       this.locationx = location.x - property.x
      //       this.locationy = location.y - property.y
      //
      //       gsap.to(selector, {left: this.playerLocation.x-15, top: this.playerLocation.y-10})
      //   }
    },
      methods: {
      checkLocation: function(that) {
        if(that.hitTest(this.$refs.htarget, '100%')){
          //location-center
          if(that.hitTest(this.$refs.prop2, '1%')) {
              let property = document.getElementById('prop2').getBoundingClientRect()
              this.calculateLocation(property, 2);
          } else if (that.hitTest(this.$refs.prop3, '1%')) {
              let property = document.getElementById('prop3').getBoundingClientRect()
              this.calculateLocation(property, 3);
          } else if (that.hitTest(this.$refs.prop4, '1%')) {
              let property = document.getElementById('prop4').getBoundingClientRect()
              this.calculateLocation(property, 4);
          } else if (that.hitTest(this.$refs.prop5, '1%')) {
              let property = document.getElementById('prop5').getBoundingClientRect()
              this.calculateLocation(property, 5);
          } else {
              gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref
              gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
          }

        } else{
              gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref
             gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
      },
      calculateLocation(property, property_id) { // prop_id is more like the player_id
        gsap.to('#locationrect', {fill: 'red'})
        let location = this.$refs.location.getBoundingClientRect()
        this.locationx = location.x - property.x + .25
        this.locationy = location.y - property.y + .25 //todo add variable radius here
          this.$emit('location-update', {x: this.locationx, y: this.locationy, property: property_id});
      }
},
    template: 
      `
      <div class="steal" style="display:flex; flex-wrap: wrap">
        <div class="game">
            <div class="">
                <div id="steal-container">
                    <div ref='htarget' class="property-container">
                      <div v-for="property in properties" v-bind:class="['property', playerGroupId==(property+1) ? 'self' : 'other']" v-bind:player-id="(property+1)" :id='"prop" + (property+1)' :ref='"prop" + (property+1)'>{{property+1}}</div>
                    </div>
                    <div class="steal-notification">
                        {{stealNotification}}
                    </div>
                    <div class="location-start">
                      <div>
                        player group id: {{playerGroupId}} <br>
                        drag location<br>
                        x: {{locationx}}<br> 
                        y: {{locationy}}<br>
                      </div>
                      <svg id="location" height="21" width="21">
                        <rect id="locationrect" x="0" y="0" width="21" height="21" style="fill:green;stroke:black;stroke-width:1;fill-opacity:0.1;stroke-opacity:0.9" />
                        <line x1="0" y1="0" x2="21" y2="21" style="stroke:red;stroke-width:1;stroke-opacity:.3"/>       
                        <line x1="21" y1="0" x2="0" y2="21" style="stroke:red;stroke-width:1;stroke-opacity:.3"/>       
                        
                        <circle ref="location" cx="10" cy="10" r=".5" fill="black" />
                        Sorry, your browser does not support inline SVG.  
                      </svg> 
                    </div>
                </div>
            </div>
        </div>
      </div>
      `
  }